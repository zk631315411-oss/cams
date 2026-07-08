/**
 * 知识图谱面板 - 简洁版（教研反馈：颜色收敛）
 */
function enhanceWithKG(cid){
  if(!kgData) return;

  var cidSec = kgData[cid];
  if(!cidSec || !cidSec.section) return;

  var secName = cidSec.section;
  var secInfo = (kgData._sections||{})[secName]||{};
  var secEdges = cidSec.edges||[];

  var tK = document.getElementById('tK');
  if(!tK) return;

  var oldTG = document.getElementById('tG');
  if(oldTG) oldTG.remove();

  var h = '';

  // Section node
  h += '<div class="kp-group">';
  h += '<div class="kp-q-head">所属概念节点</div>';
  h += '<div class="kp-card current">';
  h += '<div class="kp-body">';
  h += '<div class="kp-title">' + secName + '</div>';
  h += '<div class="kp-meta">' + (secInfo.definition||'') + '</div>';
  if(secInfo.aliases && secInfo.aliases.length){
    h += '<div class="kp-meta" style="color:#888">别名: ' + secInfo.aliases.join(', ') + '</div>';
  }
  h += '</div></div></div>';

  // Edges - simple gray, no colors
  if(secEdges.length > 0){
    h += '<div class="kp-group">';
    h += '<div class="kp-q-head">关联关系</div>';
    var shown = {};
    secEdges.forEach(function(e){
      var key = [secName, e.target].sort().join('||');
      if(shown[key]) return;
      shown[key] = true;
      h += '<div class="kp-card">';
      h += '<div class="kp-body">';
      h += '<div class="kp-title" style="font-size:13px;font-weight:normal">' + e.target + '</div>';
      h += '<div class="kp-meta">' + e.type + ': ' + (e.detail||'') + '</div>';
      h += '</div></div>';
    });
    h += '</div>';
  }

  // Hybrid results summary
  var hr = (kgData._hybrid_results||{});
  var hrKeys = Object.keys(hr);
  if(hrKeys.length > 0){
    h += '<div class="kp-group">';
    h += '<div class="kp-q-head">混合策略验证 (' + hrKeys.length + '题)</div>';
    hrKeys.forEach(function(qid){
      var r = hr[qid];
      var label = r.method === 'graph' ? '图谱' : '兜底';
      h += '<div class="kp-card">';
      h += '<div class="kp-body">';
      h += '<span class="kp-title" style="font-size:12px">' + qid + '</span>';
      h += '<span style="color:#888;font-size:11px;margin-left:6px">[' + label + ']</span>';
      h += '<div class="kp-meta" style="font-size:11px">' + (r.chain||'').substring(0,120) + '</div>';
      h += '</div></div>';
    });
    h += '</div>';
  }

  var tG = document.createElement('div');
  tG.id = 'tG';
  tG.style.display = 'none';
  tG.innerHTML = h;
  var tQ = document.getElementById('tQ');
  if(tQ){ tQ.parentNode.insertBefore(tG, tQ); }
  else { tK.parentNode.appendChild(tG); }

  // Add tab
  var tabBar = document.querySelector('.tab-bar');
  if(tabBar && !document.getElementById('tabG')){
    var tabG = document.createElement('div');
    tabG.id = 'tabG';
    tabG.className = 'tab';
    tabG.textContent = '图谱';
    tabG.onclick = function(){ swTab('g', this); };
    tabBar.insertBefore(tabG, tabBar.children[1]);
  }
}

// Hook into showDetail
var _origShowDetail = showDetail;
showDetail = function(cid){
  _origShowDetail(cid);
  setTimeout(function(){ enhanceWithKG(cid); }, 100);
};
