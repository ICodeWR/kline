import os
import json
from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
from pyecharts import options as opts
from pyecharts.charts import Kline
from stock_data import StockDataFetcher

app = Flask(__name__)
bootstrap = Bootstrap(app)

TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
stock_fetcher = StockDataFetcher(token=TUSHARE_TOKEN if TUSHARE_TOKEN else None)


def create_kline_chart(dates, data, stock_name):
    if not dates or not data:
        return None

    kline = (
        Kline(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(dates)
        .add_yaxis(
            series_name=stock_name,
            y_axis=data,
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ef232a",
                color0="#14b143",
                border_color="#ef232a",
                border_color0="#14b143",
            ),
            markline_opts=opts.MarkLineOpts(
                data=[
                    opts.MarkLineItem(type_="max", name="最高价"),
                    opts.MarkLineItem(type_="min", name="最低价"),
                ]
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=f"{stock_name} K线图",
                subtitle="数据来源: akshare / tushare.pro",
                pos_left="center",
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                axislabel_opts=opts.LabelOpts(rotate=45, interval=10),
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=0.3)
                ),
                axislabel_opts=opts.LabelOpts(formatter="{value}元"),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
                opts.DataZoomOpts(type_="slider", range_start=0, range_end=100),
            ],
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    return kline


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("404.html", error="服务器内部错误"), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/kline", methods=["POST"])
def get_kline():
    try:
        stock_keyword = request.form.get("stockName", "").strip()
        query_days = request.form.get("queryTime", "250").strip()

        if not stock_keyword:
            stock_keyword = "平安银行"

        try:
            query_days = int(query_days)
            if query_days < 10:
                query_days = 10
            elif query_days > 1000:
                query_days = 1000
        except ValueError:
            query_days = 250

        status, stock_info = stock_fetcher.search_stock(stock_keyword)
        if status == 0:
            return jsonify({"error": f"未找到股票: {stock_keyword}"}), 404

        stock_code, stock_name = stock_info

        dates, ohlc_data = stock_fetcher.get_historical_data(stock_code, query_days)
        if not dates:
            return jsonify({"error": f"获取 {stock_name}({stock_code}) 数据失败"}), 404

        kline = create_kline_chart(dates, ohlc_data, stock_name)
        if kline is None:
            return jsonify({"error": "生成K线图失败"}), 500

        return jsonify(json.loads(kline.dump_options()))

    except Exception as e:
        print(f"请求处理失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/suggest", methods=["GET"])
def get_suggestions():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify([])

    try:
        stock_df = stock_fetcher.get_stock_list()
        suggestions = []

        for _, row in stock_df.iterrows():
            code = str(row['code'])
            name = str(row['name'])
            if keyword in code or keyword in name:
                suggestions.append({
                    "code": code,
                    "name": name,
                    "display": f"{code} - {name}",
                })
                if len(suggestions) >= 10:
                    break

        return jsonify(suggestions)
    except Exception as e:
        print(f"获取建议失败: {e}")
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)