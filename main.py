"""
Trading Bot - Android App
Native Android application for cryptocurrency trading signals
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
import requests
import json
from datetime import datetime

# Set window size for testing
Window.size = (360, 640)

class TradingSignal:
    """Handle API calls to Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3/klines"
    
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol
        
    def fetch_data(self, interval="1h", limit=100):
        """Fetch price data from Binance"""
        try:
            params = {
                "symbol": self.symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            
            # Parse data
            prices = []
            for candle in data:
                prices.append({
                    'timestamp': candle[0],
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            return prices
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        closes = [p['close'] for p in prices]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return 0
        closes = [p['close'] for p in prices[-period:]]
        return sum(closes) / period
    
    def generate_signal(self, interval="1h"):
        """Generate trading signal"""
        prices = self.fetch_data(interval=interval, limit=100)
        
        if not prices:
            return {
                'symbol': self.symbol,
                'price': 0,
                'signal': 'ERROR',
                'strength': 0,
                'rsi': 0,
                'sma_20': 0,
                'sma_50': 0,
                'recommendation': 'Unable to fetch data'
            }
        
        current_price = prices[-1]['close']
        rsi = self.calculate_rsi(prices)
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, 50)
        
        # Generate signal
        buy_signals = 0
        sell_signals = 0
        
        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1
            
        if sma_20 > sma_50:
            buy_signals += 1
        elif sma_20 < sma_50:
            sell_signals += 1
        
        if buy_signals >= 2:
            signal = 'BUY'
            strength = buy_signals
            recommendation = f"Strong BUY signal detected"
        elif sell_signals >= 2:
            signal = 'SELL'
            strength = sell_signals
            recommendation = f"Strong SELL signal detected"
        else:
            signal = 'HOLD'
            strength = 0
            recommendation = "No clear signal - HOLD position"
        
        return {
            'symbol': self.symbol,
            'price': current_price,
            'signal': signal,
            'strength': strength,
            'rsi': rsi,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'recommendation': recommendation,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class MainScreen(Screen):
    """Main screen showing trading signals"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_symbol = 'BTCUSDT'
        self.current_interval = '1h'
        self.build_ui()
        
        # Auto-refresh every 5 minutes
        Clock.schedule_interval(self.refresh_signal, 300)
        
        # Load initial signal
        Clock.schedule_once(lambda dt: self.refresh_signal(), 1)
    
    def build_ui(self):
        """Build the user interface"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = BoxLayout(size_hint_y=0.1)
        with header.canvas.before:
            Color(0.4, 0.49, 0.92, 1)  # Purple color
            self.header_rect = RoundedRectangle(pos=header.pos, size=header.size, radius=[10])
        header.bind(pos=self.update_rect, size=self.update_rect)
        
        title = Label(
            text='[b]🤖 Trading Bot[/b]',
            markup=True,
            font_size='24sp',
            color=(1, 1, 1, 1)
        )
        header.add_widget(title)
        layout.add_widget(header)
        
        # Symbol selector
        symbol_layout = GridLayout(cols=4, size_hint_y=0.12, spacing=5)
        for symbol in ['BTC', 'ETH', 'SOL', 'ADA']:
            btn = Button(
                text=symbol,
                background_color=(0.4, 0.49, 0.92, 1),
                font_size='16sp'
            )
            btn.bind(on_press=lambda x, s=symbol: self.change_symbol(s))
            symbol_layout.add_widget(btn)
        layout.add_widget(symbol_layout)
        
        # Interval selector
        interval_layout = GridLayout(cols=5, size_hint_y=0.1, spacing=5)
        for interval in ['5m', '15m', '1h', '4h', '1d']:
            btn = Button(
                text=interval,
                background_color=(0.3, 0.3, 0.3, 1),
                font_size='14sp'
            )
            btn.bind(on_press=lambda x, i=interval: self.change_interval(i))
            interval_layout.add_widget(btn)
        layout.add_widget(interval_layout)
        
        # Signal display
        self.signal_container = BoxLayout(orientation='vertical', spacing=10)
        self.signal_container.add_widget(Label(
            text='Loading...',
            font_size='20sp'
        ))
        
        scroll = ScrollView(size_hint=(1, 0.58))
        scroll.add_widget(self.signal_container)
        layout.add_widget(scroll)
        
        # Refresh button
        refresh_btn = Button(
            text='↻ Refresh',
            size_hint_y=0.1,
            background_color=(0.4, 0.49, 0.92, 1),
            font_size='18sp'
        )
        refresh_btn.bind(on_press=lambda x: self.refresh_signal())
        layout.add_widget(refresh_btn)
        
        self.add_widget(layout)
    
    def update_rect(self, instance, value):
        """Update rectangle position/size"""
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size
    
    def change_symbol(self, symbol):
        """Change trading symbol"""
        self.current_symbol = f"{symbol}USDT"
        self.refresh_signal()
    
    def change_interval(self, interval):
        """Change timeframe"""
        self.current_interval = interval
        self.refresh_signal()
    
    def refresh_signal(self, *args):
        """Refresh trading signal"""
        self.signal_container.clear_widgets()
        
        # Show loading
        loading = Label(
            text='⏳ Loading signal...',
            font_size='18sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        self.signal_container.add_widget(loading)
        
        # Fetch signal in background
        def fetch():
            trader = TradingSignal(self.current_symbol)
            signal = trader.generate_signal(self.current_interval)
            Clock.schedule_once(lambda dt: self.display_signal(signal), 0)
        
        import threading
        thread = threading.Thread(target=fetch)
        thread.start()
    
    def display_signal(self, signal):
        """Display the trading signal"""
        self.signal_container.clear_widgets()
        
        # Price
        price_label = Label(
            text=f"[b]${signal['price']:,.2f}[/b]",
            markup=True,
            font_size='48sp',
            size_hint_y=0.3
        )
        self.signal_container.add_widget(price_label)
        
        # Signal
        signal_colors = {
            'BUY': (0.22, 0.93, 0.49, 1),  # Green
            'SELL': (0.92, 0.36, 0.26, 1),  # Red
            'HOLD': (0.7, 0.7, 0.7, 1),     # Gray
            'ERROR': (1, 0.5, 0, 1)          # Orange
        }
        
        signal_box = BoxLayout(orientation='vertical', size_hint_y=0.2)
        signal_label = Label(
            text=f"[b]{signal['signal']}[/b]",
            markup=True,
            font_size='32sp',
            color=signal_colors.get(signal['signal'], (1, 1, 1, 1))
        )
        
        if signal['signal'] != 'HOLD' and signal['signal'] != 'ERROR':
            strength_label = Label(
                text=f"Strength: {signal['strength']}/4",
                font_size='16sp',
                color=(0.8, 0.8, 0.8, 1)
            )
            signal_box.add_widget(signal_label)
            signal_box.add_widget(strength_label)
        else:
            signal_box.add_widget(signal_label)
        
        self.signal_container.add_widget(signal_box)
        
        # Indicators
        indicators = GridLayout(cols=2, spacing=10, size_hint_y=0.3)
        
        indicators_data = [
            ('RSI', f"{signal['rsi']:.2f}"),
            ('SMA 20', f"${signal['sma_20']:.2f}"),
            ('SMA 50', f"${signal['sma_50']:.2f}"),
            ('Time', signal['timestamp'].split()[1])
        ]
        
        for label, value in indicators_data:
            indicator_box = BoxLayout(orientation='vertical', padding=5)
            with indicator_box.canvas.before:
                Color(0.2, 0.2, 0.2, 0.5)
                RoundedRectangle(pos=indicator_box.pos, size=indicator_box.size, radius=[5])
            
            indicator_box.add_widget(Label(
                text=label,
                font_size='14sp',
                color=(0.7, 0.7, 0.7, 1)
            ))
            indicator_box.add_widget(Label(
                text=value,
                font_size='18sp',
                bold=True
            ))
            indicators.add_widget(indicator_box)
        
        self.signal_container.add_widget(indicators)
        
        # Recommendation
        rec_box = BoxLayout(orientation='vertical', size_hint_y=0.2, padding=10)
        with rec_box.canvas.before:
            Color(0.4, 0.49, 0.92, 0.2)
            RoundedRectangle(pos=rec_box.pos, size=rec_box.size, radius=[10])
        
        rec_box.add_widget(Label(
            text='💡 Recommendation',
            font_size='16sp',
            bold=True
        ))
        rec_box.add_widget(Label(
            text=signal['recommendation'],
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        self.signal_container.add_widget(rec_box)


class TradingBotApp(App):
    """Main application class"""
    
    def build(self):
        """Build the app"""
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    TradingBotApp().run()
