/* Shared visual preference. Dark is the default for both pages. */
(() => {
  const KEY='fuel-route-theme';
  const root=document.documentElement;
  let mode=root.dataset.theme === 'light' ? 'light' : 'dark';
  const button=document.getElementById('themeToggle');
  const labels={
    en:{light:'Switch to light mode',dark:'Switch to dark mode',lightShort:'Light',darkShort:'Dark'},
    es:{light:'Cambiar a modo claro',dark:'Cambiar a modo oscuro',lightShort:'Claro',darkShort:'Oscuro'},
    fr:{light:'Passer au thème clair',dark:'Passer au thème sombre',lightShort:'Clair',darkShort:'Sombre'},
    pt:{light:'Mudar para o modo claro',dark:'Mudar para o modo escuro',lightShort:'Claro',darkShort:'Escuro'}
  };
  function redraw(){
    root.dataset.theme=mode;
    if(!button)return;
    const language=(root.lang||'en').slice(0,2).toLowerCase();
    const translations=labels[language]||labels.en;
    const target=mode==='dark'?'light':'dark';
    button.setAttribute('aria-pressed',String(mode==='light'));
    button.setAttribute('aria-label',translations[target]);
    button.title=translations[target];
    const text=button.querySelector('[data-theme-text]');
    if(text)text.textContent=translations[target+'Short'];
    const darkIcon=button.querySelector('[data-theme-dark-icon]');
    const lightIcon=button.querySelector('[data-theme-light-icon]');
    if(darkIcon)darkIcon.hidden=mode!=='light';
    if(lightIcon)lightIcon.hidden=mode!=='dark';
  }
  button?.addEventListener('click',()=>{
    mode=mode==='dark'?'light':'dark';
    try{localStorage.setItem(KEY,mode);}catch(_){}
    redraw();
  });
  document.addEventListener('fuel:language-change',redraw);
  redraw();
})();