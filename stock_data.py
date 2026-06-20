import tushare as ts
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Optional, Tuple, List


class StockDataFetcher:
    """A股股票数据获取类，支持tushare和akshare双数据源"""

    def __init__(self, token: Optional[str] = None):
        self.pro = None
        if token:
            try:
                ts.set_token(token)
                self.pro = ts.pro_api()
            except Exception as e:
                print(f"tushare初始化失败，将使用akshare: {e}")
                self.pro = None
        self._stock_cache = None

    def _is_shanghai(self, code: str) -> bool:
        return code.startswith(('6', '9'))

    def _get_ts_code(self, code: str) -> str:
        suffix = '.SH' if self._is_shanghai(code) else '.SZ'
        return f"{code}{suffix}"

    def get_stock_list(self) -> pd.DataFrame:
        if self._stock_cache is not None:
            return self._stock_cache

        try:
            df = ak.stock_info_a_code_name()
            df = df.rename(columns={'code': 'code', 'name': 'name'})
            self._stock_cache = df[['code', 'name']]
            return self._stock_cache
        except Exception:
            pass

        fallback = pd.DataFrame({
            'code': ['000001', '600000', '000002', '600036', '000858',
                     '600519', '000333', '601318', '600276', '002415'],
            'name': ['平安银行', '浦发银行', '万科A', '招商银行', '五粮液',
                     '贵州茅台', '美的集团', '中国平安', '恒瑞医药', '海康威视']
        })
        self._stock_cache = fallback
        return fallback

    def get_historical_data(self, stock_code: str, days: int = 250) -> Tuple[List[str], List[List[float]]]:
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')

            symbol = self._get_ts_code(stock_code)

            df = None
            if self.pro:
                try:
                    df = self.pro.daily(
                        ts_code=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        fields='trade_date,open,high,low,close'
                    )
                except Exception:
                    pass

            if df is None or df.empty:
                try:
                    df = ak.stock_zh_a_hist(
                        symbol=stock_code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    df = df.rename(columns={
                        '日期': 'trade_date',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close'
                    })
                    df['trade_date'] = df['trade_date'].astype(str).str.replace('-', '')
                except Exception as e:
                    print(f"akshare获取数据失败: {e}")
                    return [], []

            if df.empty:
                return [], []

            df = df.sort_values('trade_date', ascending=True)
            df = df.tail(days)

            dates = df['trade_date'].tolist()
            ohlc_data = df[['open', 'high', 'low', 'close']].values.tolist()

            return dates, ohlc_data

        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return [], []

    def search_stock(self, keyword: str) -> Tuple[int, Optional[list]]:
        if not keyword:
            return 0, None

        stock_df = self.get_stock_list()
        stock_list = stock_df.values.tolist()

        for code, name in stock_list:
            if keyword in str(code) or keyword in str(name):
                return 1, [str(code), str(name)]

        return 0, None