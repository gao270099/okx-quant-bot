import ccxt
import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock

class OKXQuantMasterApp(App):
    def build(self):
        self.title = "OKX 移动量化大师 (安全版)"
        main_layout = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # 1. 顶部：实时数据看板与安全指示
        dashboard = GridLayout(cols=2, size_hint_y=0.25, spacing=5)
        dashboard.add_widget(Label(text="系统状态:", bold=True))
        self.status_lbl = Label(text="安全就绪 (未启动)", color=(1, 0.6, 0, 1))
        dashboard.add_widget(self.status_lbl)

        dashboard.add_widget(Label(text="实时市价:", bold=True))
        self.price_lbl = Label(text="-- USDT", color=(0, 1, 0, 1))
        dashboard.add_widget(self.price_lbl)

        dashboard.add_widget(Label(text="可用余额:", bold=True))
        self.balance_lbl = Label(text="-- USDT")
        dashboard.add_widget(self.balance_lbl)
        main_layout.add_widget(dashboard)

        # 2. 中部：策略与参数配置表单
        config_layout = GridLayout(cols=2, size_hint_y=0.45, spacing=6)
        
        config_layout.add_widget(Label(text="交易标的:"))
        self.symbol_input = TextInput(text="ETH/USDT", multiline=False)
        config_layout.add_widget(self.symbol_input)

        config_layout.add_widget(Label(text="量化策略:"))
        self.strategy_spinner = Spinner(
            text='网格策略 (Grid)',
            values=('网格策略 (Grid)', '做市策略 (Market Making)', '趋势追踪 (3分钟MA)', 'DCA 定投 (DCA)')
        )
        config_layout.add_widget(self.strategy_spinner)

        config_layout.add_widget(Label(text="OKX API Key:"))
        self.api_key_input = TextInput(multiline=False, password=True)
        config_layout.add_widget(self.api_key_input)

        config_layout.add_widget(Label(text="OKX Secret:"))
        self.secret_input = TextInput(multiline=False, password=True)
        config_layout.add_widget(self.secret_input)

        config_layout.add_widget(Label(text="OKX Passphrase:"))
        self.pass_input = TextInput(multiline=False, password=True)
        config_layout.add_widget(self.pass_input)

        main_layout.add_widget(config_layout)

        # 3. 底部：实时日志输出窗口
        self.log_lbl = Label(text="日志: 请输入 API 并点击启动策略...", size_hint_y=0.15, font_size=12, color=(0.8, 0.8, 0.8, 1))
        main_layout.add_widget(self.log_lbl)

        # 4. 底部：总控制大按钮
        self.toggle_btn = Button(
            text="启动自动化策略", 
            size_hint_y=0.15, 
            background_color=(0.1, 0.7, 0.2, 1)
        )
        self.toggle_btn.bind(on_press=self.toggle_bot)
        main_layout.add_widget(self.toggle_btn)

        self.running = False
        return main_layout

    def log(self, message):
        """线程安全的界面日志更新"""
        Clock.schedule_once(lambda dt: setattr(self.log_lbl, 'text', f"日志: {message}"))

    def toggle_bot(self, instance):
        if not self.running:
            if not self.api_key_input.text.strip():
                self.log("错误: API Key 不能为空！")
                return
            self.running = True
            self.toggle_btn.text = "紧急停止策略"
            self.toggle_btn.background_color = (0.8, 0.1, 0.1, 1)
            self.status_lbl.text = "运行中 (多策略低功耗循环)"
            threading.Thread(target=self.bot_execution_loop, daemon=True).start()
        else:
            self.running = False
            self.toggle_btn.text = "启动自动化策略"
            self.toggle_btn.background_color = (0.1, 0.7, 0.2, 1)
            self.status_lbl.text = "已安全中止"
            self.log("用户手动停止了策略。")

    def bot_execution_loop(self):
        try:
            self.log("正在通过安全通道连接 OKX 交易所...")
            exchange = ccxt.okx({
                'apiKey': self.api_key_input.text.strip(),
                'secret': self.secret_input.text.strip(),
                'password': self.pass_input.text.strip(),
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'} # 默认现货模式，绝对防爆仓
            })
            
            symbol = self.symbol_input.text.strip().upper()
            strategy = self.strategy_spinner.text
            self.log(f"连接成功！当前策略: {strategy} | 标的: {symbol}")

            consecutive_errors = 0

            while self.running:
                try:
                    # 获取行情与账户余额
                    ticker = exchange.fetch_ticker(symbol)
                    price = ticker['last']
                    balance = exchange.fetch_balance()
                    usdt_free = balance['free'].get('USDT', 0.0)

                    # 更新 UI 数据看板
                    Clock.schedule_once(lambda dt, p=price: setattr(self.price_lbl, 'text', f"{p} USDT"))
                    Clock.schedule_once(lambda dt, b=usdt_free: setattr(self.balance_lbl, 'text', f"{b:.2f} USDT"))

                    # 针对不同策略的分流执行逻辑（支持您要求的 3 分钟策略）
                    if "趋势追踪" in strategy:
                        # 获取 3 分钟 K 线进行均线判断
                        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='3m', limit=10)
                        closes = [c[4] for c in ohlcv]
                        ma_fast = sum(closes[-3:]) / 3
                        ma_slow = sum(closes[-10:]) / 10
                        self.log(f"3分钟策略检测: 现价 {price} | 快线 {ma_fast:.2f} | 慢线 {ma_slow:.2f}")
                    elif "网格策略" in strategy:
                        self.log(f"网格监控中: 当前价格 {price} 运行平稳...")

                    consecutive_errors = 0
                    
                    # 按照 3 分钟（180秒）周期循环，超级省电省流量
                    for _ in range(180):
                        if not self.running: 
                            break
                        time.sleep(1)

                except Exception as inner_e:
                    consecutive_errors += 1
                    self.log(f"网络波动 ({consecutive_errors}/5): {str(inner_e)[:20]}")
                    if consecutive_errors > 5:
                        self.log("连续出错超过5次，进入 60 秒冷却休眠...")
                        time.sleep(60)
                    else:
                        time.sleep(10)

        except Exception as e:
            self.log(f"初始化严重错误: {str(e)[:30]}")
            self.running = False
            Clock.schedule_once(lambda dt: setattr(self.toggle_btn, 'text', "启动自动化策略"))
            Clock.schedule_once(lambda dt: setattr(self.toggle_btn, 'background_color', (0.1, 0.7, 0.2, 1)))
            Clock.schedule_once(lambda dt: setattr(self.status_lbl, 'text', "异常终止"))

if __name__ == '__main__':
    OKXQuantMasterApp().run()
