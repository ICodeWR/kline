import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stock_data import StockDataFetcher


class TestStockDataFetcherInit(unittest.TestCase):
    """测试 StockDataFetcher 初始化"""

    def test_init_without_token(self):
        fetcher = StockDataFetcher()
        self.assertIsNone(fetcher.pro)
        self.assertIsNone(fetcher._stock_cache)

    def test_init_with_empty_token(self):
        fetcher = StockDataFetcher(token="")
        self.assertIsNone(fetcher.pro)

    def test_init_with_none_token(self):
        fetcher = StockDataFetcher(token=None)
        self.assertIsNone(fetcher.pro)

    @patch('stock_data.ts')
    def test_init_with_token_success(self, mock_ts):
        mock_ts.pro_api.return_value = MagicMock()
        fetcher = StockDataFetcher(token="valid_token")
        mock_ts.set_token.assert_called_once_with("valid_token")
        mock_ts.pro_api.assert_called_once()
        self.assertIsNotNone(fetcher.pro)

    @patch('stock_data.ts')
    def test_init_with_token_failure(self, mock_ts):
        mock_ts.set_token.side_effect = PermissionError("Permission denied")
        fetcher = StockDataFetcher(token="bad_token")
        self.assertIsNone(fetcher.pro)


class TestStockDataFetcherHelpers(unittest.TestCase):
    """测试辅助方法"""

    def setUp(self):
        self.fetcher = StockDataFetcher()

    def test_is_shanghai_true(self):
        self.assertTrue(self.fetcher._is_shanghai("600000"))
        self.assertTrue(self.fetcher._is_shanghai("688001"))
        self.assertTrue(self.fetcher._is_shanghai("900001"))

    def test_is_shanghai_false(self):
        self.assertFalse(self.fetcher._is_shanghai("000001"))
        self.assertFalse(self.fetcher._is_shanghai("002415"))
        self.assertFalse(self.fetcher._is_shanghai("300750"))

    def test_get_ts_code_shanghai(self):
        self.assertEqual(self.fetcher._get_ts_code("600000"), "600000.SH")
        self.assertEqual(self.fetcher._get_ts_code("688001"), "688001.SH")

    def test_get_ts_code_shenzhen(self):
        self.assertEqual(self.fetcher._get_ts_code("000001"), "000001.SZ")
        self.assertEqual(self.fetcher._get_ts_code("002415"), "002415.SZ")


class TestStockDataFetcherStockList(unittest.TestCase):
    """测试股票列表获取"""

    def setUp(self):
        self.fetcher = StockDataFetcher()

    @patch('stock_data.ak.stock_info_a_code_name')
    def test_get_stock_list_success(self, mock_ak):
        mock_df = pd.DataFrame({
            'code': ['000001', '600000'],
            'name': ['平安银行', '浦发银行']
        })
        mock_ak.return_value = mock_df
        result = self.fetcher.get_stock_list()
        self.assertEqual(len(result), 2)
        self.assertIn('code', result.columns)
        self.assertIn('name', result.columns)
        self.assertEqual(result.iloc[0]['code'], '000001')

    @patch('stock_data.ak.stock_info_a_code_name')
    def test_get_stock_list_cache(self, mock_ak):
        mock_df = pd.DataFrame({
            'code': ['000001'],
            'name': ['平安银行']
        })
        mock_ak.return_value = mock_df
        self.fetcher.get_stock_list()
        self.fetcher.get_stock_list()
        mock_ak.assert_called_once()

    @patch('stock_data.ak.stock_info_a_code_name')
    def test_get_stock_list_fallback(self, mock_ak):
        mock_ak.side_effect = Exception("Network error")
        self.fetcher._stock_cache = None
        result = self.fetcher.get_stock_list()
        self.assertEqual(len(result), 10)
        self.assertIn('000001', result['code'].values)
        self.assertIn('600519', result['code'].values)


class TestStockDataFetcherSearch(unittest.TestCase):
    """测试股票搜索"""

    def setUp(self):
        self.fetcher = StockDataFetcher()

    def _set_fallback_cache(self):
        fallback = pd.DataFrame({
            'code': ['000001', '600000', '000002', '600036', '000858',
                     '600519', '000333', '601318', '600276', '002415'],
            'name': ['平安银行', '浦发银行', '万科A', '招商银行', '五粮液',
                     '贵州茅台', '美的集团', '中国平安', '恒瑞医药', '海康威视']
        })
        self.fetcher._stock_cache = fallback

    def test_search_by_code_exact(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("000001")
        self.assertEqual(status, 1)
        self.assertEqual(info[0], "000001")
        self.assertEqual(info[1], "平安银行")

    def test_search_by_code_partial(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("00000")
        self.assertEqual(status, 1)
        self.assertEqual(info[0], "000001")

    def test_search_by_name_exact(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("贵州茅台")
        self.assertEqual(status, 1)
        self.assertEqual(info[0], "600519")

    def test_search_by_name_partial(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("茅台")
        self.assertEqual(status, 1)
        self.assertEqual(info[0], "600519")

    def test_search_not_found(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("ZZZZZZ")
        self.assertEqual(status, 0)
        self.assertIsNone(info)

    def test_search_empty_keyword(self):
        self._set_fallback_cache()
        status, info = self.fetcher.search_stock("")
        self.assertEqual(status, 0)
        self.assertIsNone(info)


class TestStockDataFetcherHistorical(unittest.TestCase):
    """测试历史数据获取"""

    def setUp(self):
        self.fetcher = StockDataFetcher()

    def test_get_historical_data_no_token_no_network(self):
        dates, ohlc = self.fetcher.get_historical_data("000001", 10)
        self.assertIsInstance(dates, list)
        self.assertIsInstance(ohlc, list)
        self.assertEqual(len(dates), len(ohlc))

    @patch('stock_data.ak.stock_zh_a_hist')
    def test_get_historical_data_success(self, mock_ak):
        mock_df = pd.DataFrame({
            '日期': ['20250102', '20250103', '20250106'],
            '开盘': [10.0, 10.5, 11.0],
            '最高': [10.8, 11.0, 11.5],
            '最低': [9.8, 10.2, 10.8],
            '收盘': [10.5, 11.0, 11.2]
        })
        mock_ak.return_value = mock_df

        dates, ohlc = self.fetcher.get_historical_data("000001", 10)
        self.assertEqual(len(dates), 3)
        self.assertEqual(len(ohlc), 3)
        self.assertEqual(dates[0], '20250102')
        self.assertEqual(ohlc[0], [10.0, 10.8, 9.8, 10.5])

    @patch('stock_data.ak.stock_zh_a_hist')
    def test_get_historical_data_network_error(self, mock_ak):
        mock_ak.side_effect = Exception("Connection error")
        dates, ohlc = self.fetcher.get_historical_data("000001", 10)
        self.assertEqual(dates, [])
        self.assertEqual(ohlc, [])

    @patch('stock_data.ak.stock_zh_a_hist')
    def test_get_historical_data_empty_result(self, mock_ak):
        mock_ak.return_value = pd.DataFrame()
        dates, ohlc = self.fetcher.get_historical_data("000001", 10)
        self.assertEqual(dates, [])
        self.assertEqual(ohlc, [])

    @patch('stock_data.ak.stock_zh_a_hist')
    def test_get_historical_data_with_tail(self, mock_ak):
        data = {
            '日期': [f'20250{i:03d}' for i in range(101, 301)],
            '开盘': [10.0] * 200,
            '最高': [11.0] * 200,
            '最低': [9.0] * 200,
            '收盘': [10.5] * 200,
        }
        mock_df = pd.DataFrame(data)
        mock_ak.return_value = mock_df

        dates, ohlc = self.fetcher.get_historical_data("000001", 30)
        self.assertEqual(len(dates), 30)
        self.assertEqual(len(ohlc), 30)


if __name__ == '__main__':
    unittest.main()