/** Tema "noir" (Blade Runner-stilen från film 01) – fylls på när GNISTAN flyttas in i motorn. */
(function () {
  const M = window.Motor;
  M.teman.noir = M.teman.noir || { rita: c => { c.fillStyle = '#05080c'; c.fillRect(0, 0, M.W, M.H); } };
})();
