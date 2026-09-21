/* 產業熱度熱力圖 —— squarified treemap
 * 演算法照抄 Bruls/Huizing/van Wijk 1999（squarify 套件的標準寫法），
 * 只是從 Python 移植成 JS，邏輯不變：先把數值正規化成面積，
 * 每次挑一小段（row）讓「這段裡最扁的那塊」最不扁，再往剩下的空間遞迴排下去。
 */
(function () {
  'use strict';

  function sum(a) { return a.reduce(function (p, v) { return p + v; }, 0); }

  function normalizeSizes(sizes, dx, dy) {
    var totalSize = sum(sizes), totalArea = dx * dy;
    if (totalSize <= 0) return sizes.map(function () { return 0; });
    return sizes.map(function (s) { return s * totalArea / totalSize; });
  }

  function layoutRow(sizes, x, y, dx, dy) {
    var covered = sum(sizes), width = dy > 0 ? covered / dy : 0;
    var rects = [], cy = y;
    sizes.forEach(function (size) {
      var h = width > 0 ? size / width : 0;
      rects.push({ x: x, y: cy, dx: width, dy: h });
      cy += h;
    });
    return rects;
  }

  function layoutCol(sizes, x, y, dx, dy) {
    var covered = sum(sizes), height = dx > 0 ? covered / dx : 0;
    var rects = [], cx = x;
    sizes.forEach(function (size) {
      var w = height > 0 ? size / height : 0;
      rects.push({ x: cx, y: y, dx: w, dy: height });
      cx += w;
    });
    return rects;
  }

  function layout(sizes, x, y, dx, dy) {
    return dx >= dy ? layoutRow(sizes, x, y, dx, dy) : layoutCol(sizes, x, y, dx, dy);
  }

  function leftover(sizes, x, y, dx, dy) {
    var covered = sum(sizes);
    if (dx >= dy) {
      var width = dy > 0 ? covered / dy : 0;
      return { x: x + width, y: y, dx: Math.max(dx - width, 0), dy: dy };
    }
    var height = dx > 0 ? covered / dx : 0;
    return { x: x, y: y + height, dx: dx, dy: Math.max(dy - height, 0) };
  }

  function worstRatio(sizes, x, y, dx, dy) {
    var rects = layout(sizes, x, y, dx, dy), worst = 0, ok = false;
    rects.forEach(function (r) {
      if (r.dx <= 0 || r.dy <= 0) return;
      ok = true;
      worst = Math.max(worst, Math.max(r.dx / r.dy, r.dy / r.dx));
    });
    return ok ? worst : Infinity;
  }

  function squarify(sizes, x, y, dx, dy) {
    sizes = sizes.filter(function (s) { return s > 0; });
    if (!sizes.length) return [];
    if (sizes.length === 1) return layout(sizes, x, y, dx, dy);

    var i = 1;
    while (i < sizes.length &&
           worstRatio(sizes.slice(0, i), x, y, dx, dy) >= worstRatio(sizes.slice(0, i + 1), x, y, dx, dy)) {
      i++;
    }
    var current = sizes.slice(0, i), remaining = sizes.slice(i);
    var lo = leftover(current, x, y, dx, dy);
    return layout(current, x, y, dx, dy).concat(squarify(remaining, lo.x, lo.y, lo.dx, lo.dy));
  }

  /* items: [{size, ...}]，size 決定面積，其餘欄位任意、原樣帶回 render 的 opts 裡用 */
  function render(host, items, opts) {
    opts = opts || {};
    var W = host.clientWidth || 900;
    var H = opts.height ? opts.height(W) : Math.round(W * 0.55);
    host.style.position = 'relative';
    host.style.height = H + 'px';

    var sorted = items.slice().sort(function (a, b) { return b.size - a.size; });
    var sizes = normalizeSizes(sorted.map(function (d) { return d.size; }), W, H);
    var rects = squarify(sizes, 0, 0, W, H);

    host.innerHTML = '';
    rects.forEach(function (r, i) {
      var d = sorted[i];
      var tile = document.createElement('a');
      tile.className = 'tm-tile';
      tile.href = d.href;
      var pad = 2;
      tile.style.left = r.x + 'px';
      tile.style.top = r.y + 'px';
      tile.style.width = Math.max(r.dx - pad, 0) + 'px';
      tile.style.height = Math.max(r.dy - pad, 0) + 'px';
      tile.style.background = opts.color ? opts.color(d) : '#3987e5';
      var tiny = r.dx < 56 || r.dy < 40;
      tile.innerHTML = tiny
        ? '<span class="tm-name">' + d.label + '</span>'
        : '<span class="tm-name">' + d.label + '</span><span class="tm-score">' + d.scoreLabel + '</span>';
      if (opts.onHover) tile.addEventListener('mouseenter', function () { opts.onHover(d, tile); });
      if (opts.onMove) tile.addEventListener('mousemove', function (e) { opts.onMove(d, tile, e); });
      if (opts.onLeave) tile.addEventListener('mouseleave', function () { opts.onLeave(d, tile); });
      host.appendChild(tile);
    });
  }

  window.Treemap = { render: render, squarify: squarify };
})();
