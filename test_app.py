import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_mock_fetcher(stock_list_df=None):
    if stock_list_df is None:
        stock_list_df = pd.DataFrame({
            'code': ['000001', '600000', '600519'],
            'name': ['平安银行', '浦发银行', '贵州茅台']
        })

    mock = MagicMock()
    mock.get_stock_list.return_value = stock_list_df

    def mock_search(keyword):
        if not keyword:
            return 0, None
        for _, row in stock_list_df.iterrows():
            if keyword in str(row['code']) or keyword in str(row['name']):
                return 1, [str(row['code']), str(row['name'])]
        return 0, None

    mock.search_stock.side_effect = mock_search

    mock.get_historical_data.return_value = (
        ['20250102', '20250103', '20250106'],
        [[10.0, 10.8, 9.8, 10.5],
         [10.5, 11.0, 10.2, 11.0],
         [11.0, 11.5, 10.8, 11.2]]
    )
    return mock


class TestFlaskApp(unittest.TestCase):
    """Flask 应用测试"""

    @classmethod
    def setUpClass(cls):
        cls._mock_fetcher = _make_mock_fetcher()
        cls._mock_fetcher_module = MagicMock()
        cls._mock_fetcher_module.StockDataFetcher.return_value = cls._mock_fetcher

        cls._patcher = patch.dict('sys.modules', {'stock_data': cls._mock_fetcher_module})
        cls._patcher.start()

        import app
        cls.app = app.app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls._patcher.stop()

    def setUp(self):
        self._mock_fetcher.get_stock_list.return_value = pd.DataFrame({
            'code': ['000001', '600000', '600519'],
            'name': ['平安银行', '浦发银行', '贵州茅台']
        })
        self._mock_fetcher.search_stock.side_effect = None
        self._mock_fetcher.search_stock.side_effect = lambda keyword: (
            (1, ['000001', '平安银行']) if keyword == '000001' or keyword == '平安银行'
            else (0, None)
        )
        self._mock_fetcher.get_historical_data.return_value = (
            ['20250102', '20250103', '20250106'],
            [[10.0, 10.8, 9.8, 10.5],
             [10.5, 11.0, 10.2, 11.0],
             [11.0, 11.5, 10.8, 11.2]]
        )

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_404_page(self):
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertIn('404'.encode('utf-8'), response.data)

    def test_suggest_empty_keyword(self):
        response = self.client.get('/api/suggest?keyword=')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def test_suggest_no_keyword(self):
        response = self.client.get('/api/suggest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def test_suggest_by_code(self):
        response = self.client.get('/api/suggest?keyword=000001')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['code'], '000001')

    def test_suggest_by_name(self):
        response = self.client.get('/api/suggest?keyword=平安')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(len(data), 0)
        self.assertIn('平安银行', [item['name'] for item in data])

    def test_suggest_not_found(self):
        response = self.client.get('/api/suggest?keyword=ZZZZZZ')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def test_suggest_max_10_results(self):
        many_df = pd.DataFrame({
            'code': [f'{i:06d}' for i in range(20)],
            'name': [f'测试{i}' for i in range(20)]
        })
        self._mock_fetcher.get_stock_list.return_value = many_df

        response = self.client.get('/api/suggest?keyword=测试')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertLessEqual(len(data), 10)

    def test_kline_success(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        response = self.client.post('/api/kline', data={
            'stockName': '000001',
            'queryTime': '30'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('series', data)
        self.assertIn('xAxis', data)
        self.assertIn('yAxis', data)

    def test_kline_empty_stock_name_defaults(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        response = self.client.post('/api/kline', data={
            'stockName': '',
            'queryTime': '30'
        })
        self.assertEqual(response.status_code, 200)

    def test_kline_stock_not_found(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (0, None)
        response = self.client.post('/api/kline', data={
            'stockName': 'ZZZZZZ',
            'queryTime': '30'
        })
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_kline_query_days_below_minimum(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        response = self.client.post('/api/kline', data={
            'stockName': '000001',
            'queryTime': '5'
        })
        self.assertEqual(response.status_code, 200)

    def test_kline_query_days_above_maximum(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        response = self.client.post('/api/kline', data={
            'stockName': '000001',
            'queryTime': '2000'
        })
        self.assertEqual(response.status_code, 200)

    def test_kline_query_days_invalid(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        response = self.client.post('/api/kline', data={
            'stockName': '000001',
            'queryTime': 'abc'
        })
        self.assertEqual(response.status_code, 200)

    def test_kline_no_data_returned(self):
        self._mock_fetcher.search_stock.side_effect = lambda kw: (1, ['000001', '平安银行'])
        self._mock_fetcher.get_historical_data.return_value = ([], [])
        response = self.client.post('/api/kline', data={
            'stockName': '000001',
            'queryTime': '30'
        })
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('数据失败', data['error'])


class TestCreateKlineChart(unittest.TestCase):
    """测试 K线图生成函数"""

    @classmethod
    def setUpClass(cls):
        cls._mock_fetcher = MagicMock()
        cls._mock_fetcher_module = MagicMock()
        cls._mock_fetcher_module.StockDataFetcher.return_value = cls._mock_fetcher

        cls._patcher = patch.dict('sys.modules', {'stock_data': cls._mock_fetcher_module})
        cls._patcher.start()

        import app
        cls._create_kline_chart = app.create_kline_chart

    @classmethod
    def tearDownClass(cls):
        cls._patcher.stop()

    def test_empty_dates_returns_none(self):
        result = self.__class__._create_kline_chart([], [[10, 11, 9, 10.5]], "测试")
        self.assertIsNone(result)

    def test_empty_data_returns_none(self):
        result = self.__class__._create_kline_chart(["20250101"], [], "测试")
        self.assertIsNone(result)

    def test_both_empty_returns_none(self):
        result = self.__class__._create_kline_chart([], [], "测试")
        self.assertIsNone(result)

    def test_valid_data_returns_kline(self):
        dates = ['20250102', '20250103', '20250106']
        data = [
            [10.0, 10.8, 9.8, 10.5],
            [10.5, 11.0, 10.2, 11.0],
            [11.0, 11.5, 10.8, 11.2]
        ]
        result = self.__class__._create_kline_chart(dates, data, "平安银行")
        self.assertIsNotNone(result)

        options = json.loads(result.dump_options())
        self.assertIn('title', options)
        self.assertIn('平安银行', options['title'][0]['text'])
        self.assertIn('series', options)
        self.assertEqual(len(options['series']), 1)
        self.assertEqual(len(options['series'][0]['data']), 3)

    def test_single_data_point(self):
        dates = ['20250102']
        data = [[10.0, 10.8, 9.8, 10.5]]
        result = self.__class__._create_kline_chart(dates, data, "测试")
        self.assertIsNotNone(result)

        options = json.loads(result.dump_options())
        self.assertEqual(len(options['series'][0]['data']), 1)


if __name__ == '__main__':
    unittest.main()