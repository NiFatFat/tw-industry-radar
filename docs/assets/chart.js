/* 個股 K 線圖渲染器 —— 改自 tv-chart skill 的 starter.js 骨架
 * 保留四個原始骨架已經踩過的坑：
 *   ① setStretchFactor 配 pane 高度（不用 setHeight）
 *   ② 只用連續的 MA 線（資料層已裁到 60MA 有值那天開始，不會有 NaN／斷點）
 *   ③ 固定高度的十字游標讀數列（不跳版）
 *   ④ ResizeObserver 觀察外層 host，不是觀察 canvas 容器
 *
 * 資料格式（見 pipeline/fetch_prices.py）：
 *   dates : ["2025-06-06", ...]
 *   bars  : [[i, o, h, l, c, colorIdx], ...]   colorIdx 0=陽 1=陰
 *   vol   : [[i, 張數, 0|1], ...]               0=紅(陽) 1=綠(陰)
 *   ma    : {"5": [[i, value], ...], "20": [...], "60": [...]}
 */
(function () {
  'use strict';
  var LC = window.LightweightCharts;

  var C = {
    panel: '#0a1222', grid: '#143352', text: '#cfe6ff', muted: '#5f80a6',
    up: '#ff5277', down: '#2ee6a8',                 // 台股紅漲綠跌，不可調動
    ma5: '#b39dff', ma20: '#ffd54f', ma60: '#25e6ff', // 疊圖刻意避開紅綠
  };
  var RATIO = [3.2, 1.0];

  function render(host, d) {
    host.classList.add('mofi-chart');
    var D = d.dates, T = function (i) { return D[i]; };
    host.innerHTML =
      '<div class="tc-readout"><div class="tc-ro-line">移到圖上看數值</div>'
      + '<div class="tc-ro-line"></div></div><div class="tc-canvas"></div>';
    var wrap = host.querySelector('.tc-canvas');
    var mob = window.innerWidth < 768;

    var chart = LC.createChart(wrap, {
      width: wrap.clientWidth, height: mob ? 420 : 560,
      layout: {
        background: { color: C.panel }, textColor: C.text,
        fontFamily: "'Fira Code','Microsoft JhengHei',ui-monospace,monospace",
        attributionLogo: false,
        panes: { separatorColor: C.grid, enableResize: !mob }
      },
      grid: { vertLines: { color: C.grid, style: 1 }, horzLines: { color: C.grid, style: 1 } },
      rightPriceScale: { borderColor: C.grid },
      timeScale: {
        borderColor: C.grid, barSpacing: mob ? 3 : 6,
        tickMarkFormatter: function (t, type) {
          var p = String(t).split('-');
          if (type === LC.TickMarkType.Year) return p[0] + '年';
          if (type === LC.TickMarkType.Month) return Number(p[1]) + '月';
          return Number(p[1]) + '/' + Number(p[2]);
        }
      },
      crosshair: { mode: LC.CrosshairMode.Normal,
                   vertLine: { color: C.ma60, style: 2 }, horzLine: { color: C.ma60, style: 2 } },
      handleScroll: { vertTouchDrag: false }
    });

    var candle = chart.addSeries(LC.CandlestickSeries, { borderVisible: true }, 0);
    candle.setData(d.bars.map(function (b) {
      var yang = b[5] === 0, c = yang ? C.up : C.down;
      return { time: T(b[0]), open: b[1], high: b[2], low: b[3], close: b[4],
               color: yang ? c : C.panel, borderColor: c, wickColor: c };
    }));

    function addMA(key, color) {
      var pts = (d.ma && d.ma[key]) || [];
      if (!pts.length) return;
      var s = chart.addSeries(LC.LineSeries, {
        color: color, lineWidth: 2, priceLineVisible: false,
        lastValueVisible: true, crosshairMarkerVisible: false
      }, 0);
      s.setData(pts.map(function (p) { return { time: T(p[0]), value: p[1] }; }));
    }
    addMA('5', C.ma5);
    addMA('20', C.ma20);
    addMA('60', C.ma60);

    var vol = chart.addSeries(LC.HistogramSeries, {
      priceFormat: { type: 'volume' }, priceLineVisible: false, lastValueVisible: false
    }, 1);
    vol.setData(d.vol.map(function (v) {
      return { time: T(v[0]), value: v[1], color: v[2] === 0 ? C.up : C.down };
    }));

    chart.panes().forEach(function (p, i) {
      if (i < RATIO.length) p.setStretchFactor(RATIO[i]);
    });

    var barAt = {}; d.bars.forEach(function (b) { barAt[b[0]] = b; });
    var volAt = {}; d.vol.forEach(function (v) { volAt[v[0]] = v[1]; });
    var maAt = { 5: {}, 20: {}, 60: {} };
    ['5', '20', '60'].forEach(function (k) {
      (d.ma[k] || []).forEach(function (p) { maAt[k][p[0]] = p[1]; });
    });
    var idxOf = {}; D.forEach(function (t, i) { idxOf[t] = i; });

    chart.subscribeCrosshairMove(function (p) {
      var i = p && p.time !== undefined ? idxOf[p.time] : undefined;
      var L = host.querySelectorAll('.tc-ro-line');
      if (i === undefined || !barAt[i]) { L[0].textContent = '移到圖上看數值'; L[1].textContent = ''; return; }
      var b = barAt[i], chg = ((b[4] - b[1]) / b[1] * 100).toFixed(2);
      L[0].textContent = D[i] + '　開 ' + b[1] + '　高 ' + b[2] + '　低 ' + b[3] + '　收 ' + b[4]
        + '　' + (chg >= 0 ? '+' : '') + chg + '%';
      var m5 = maAt[5][i], m20 = maAt[20][i], m60 = maAt[60][i];
      L[1].textContent = '量 ' + (volAt[i] != null ? volAt[i] + ' 張' : '—')
        + '　MA5 ' + (m5 != null ? m5.toFixed(1) : '—')
        + '　MA20 ' + (m20 != null ? m20.toFixed(1) : '—')
        + '　MA60 ' + (m60 != null ? m60.toFixed(1) : '—');
    });

    function layout() {
      chart.applyOptions({ width: wrap.clientWidth,
                           height: window.innerWidth < 768 ? 420 : 560 });
    }
    if (window.ResizeObserver) new ResizeObserver(layout).observe(host);
    else window.addEventListener('resize', layout);

    chart.timeScale().fitContent();
    return chart;
  }

  window.RadarChart = { render: render };
})();
