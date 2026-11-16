/* Landing-only narrative and illustration. It never calls the routing API. */
(() => {
  const translations = {"en":{"navLabel":"Primary navigation","homeLabel":"Fuel Route Optimizer home","languageLabel":"Language","navMethod":"The method","navPlanner":"Route planner","headline":"Distance tells half the story.","intro":"The other half is fuel. Explore US road routes, estimate where refueling may be needed and understand the cost assumptions before you drive.","cta":"Open the route planner","secondary":"Explore the method","heroFoot":"Built with Django, HeiGIT and OpenFreeMap","instrumentTitle":"One full tank. Up to 500 miles.","presetsLabel":"Example distances","methodHeading":"The road. The prices. The decision.","methodIntro":"Real route geometry meets the supplied fuel-price dataset. The result separates money spent on new fuel from the estimated value already in the starting tank.","method1Title":"Follow the road","method1Text":"HeiGIT provides road distance and geometry for the route you request. This is not a straight-line mileage estimate.","method2Title":"Consider fuel prices","method2Text":"The supplied dataset contains undated fuel-price observations. Station locations are approximate city coordinates.","method3Title":"Show the trade-off","method3Text":"The optimizer proposes fuel purchases and reports their cost, alongside the assumptions and limitations.","labHeading":"What does 500 miles really mean?","labIntro":"Change a hypothetical trip distance to see how the assumed range affects fuel consumption and the minimum number of refills.","labWarning":"Illustration only. These are arithmetic limits, not a road route, verified stations or optimized purchases.","distanceLabel":"Hypothetical distance","stopsLabel":"Minimum refills","gallonsLabel":"Fuel consumed","distanceUnit":"miles","gallonsUnit":"gallons","closeHeading":"Ready to test a real route?","closeText":"Choose two US cities to see the actual road geometry, estimated fuel stops and fuel costs.","closeCta":"Start planning","disclaimer":"Fuel prices are undated observations. Suggested station markers use approximate city positions, not verified pump entrances.","footerLink":"Source code","pageTitle":"Fuel Route Optimizer | Fuel-aware US route planning","journeyKicker":"FUEL RANGE / CONCEPT DIAGRAM","journeySvgTitle":"A schematic journey with five equal-distance intervals of 100 miles. Not a mapped road.","journeyDisclaimer":"Illustration only — not a mapped road or a verified fuel stop.","journeyTank":"Starting tank","journeyEfficiency":"Fuel efficiency"},"es":{"navLabel":"Navegación principal","homeLabel":"Inicio de Fuel Route Optimizer","languageLabel":"Idioma","navMethod":"El método","navPlanner":"Planificador","headline":"La distancia cuenta solo la mitad.","intro":"La otra mitad es el combustible. Explorá rutas por Estados Unidos, estimá cuándo podrías necesitar cargar y entendé los supuestos antes de salir.","cta":"Abrir el planificador","secondary":"Conocer el método","heroFoot":"Desarrollado con Django, HeiGIT y OpenFreeMap","instrumentTitle":"Un tanque lleno. Hasta 500 millas.","presetsLabel":"Distancias de ejemplo","methodHeading":"El camino. Los precios. La decisión.","methodIntro":"Las rutas reales se combinan con el archivo de precios. El resultado separa las compras nuevas del valor estimado del combustible inicial.","method1Title":"Seguir la carretera","method1Text":"HeiGIT proporciona distancias y geometría de las rutas solicitadas, no distancias en línea recta.","method2Title":"Evaluar los precios","method2Text":"El archivo contiene observaciones de precios sin fecha. Las estaciones tienen ubicaciones aproximadas por ciudad.","method3Title":"Mostrar las alternativas","method3Text":"El optimizador propone cargas de combustible e informa sus costos, supuestos y limitaciones.","labHeading":"¿Qué significan 500 millas?","labIntro":"Cambiá una distancia hipotética para entender cómo influye la autonomía sobre el consumo y las cargas mínimas.","labWarning":"Solo una ilustración aritmética. No representa un recorrido, estaciones verificadas ni compras optimizadas.","distanceLabel":"Distancia hipotética","stopsLabel":"Cargas mínimas","gallonsLabel":"Combustible consumido","distanceUnit":"millas","gallonsUnit":"galones","closeHeading":"¿Probamos una ruta real?","closeText":"Elegí dos ciudades de Estados Unidos para ver el recorrido, las paradas y los costos estimados.","closeCta":"Planificar ruta","disclaimer":"Los precios provienen de observaciones sin fecha. Los marcadores son ubicaciones aproximadas por ciudad, no surtidores verificados.","footerLink":"Código fuente","pageTitle":"Fuel Route Optimizer | Planificación de rutas en EE. UU.","journeyKicker":"AUTONOMÍA / RECORRIDO ILUSTRATIVO","journeySvgTitle":"Un recorrido esquemático con cinco tramos de 100 millas. No representa una carretera real.","journeyDisclaimer":"Esquema ilustrativo: no es una ruta real ni una estación verificada.","journeyTank":"Tanque inicial","journeyEfficiency":"Rendimiento"},"fr":{"navLabel":"Navigation principale","homeLabel":"Accueil de Fuel Route Optimizer","languageLabel":"Langue","navMethod":"La méthode","navPlanner":"Planificateur","headline":"La distance ne dit pas tout.","intro":"Le carburant compte aussi. Explorez des itinéraires aux États-Unis, estimez les besoins en ravitaillement et comprenez les hypothèses avant le départ.","cta":"Ouvrir le planificateur","secondary":"Découvrir la méthode","heroFoot":"Conçu avec Django, HeiGIT et OpenFreeMap","instrumentTitle":"Un plein. Jusqu'à 500 miles.","presetsLabel":"Distances exemples","methodHeading":"La route. Les prix. Le choix.","methodIntro":"Le tracé routier réel est associé au fichier des prix. Le résultat distingue les nouveaux achats de la valeur du carburant initial.","method1Title":"Suivre les routes","method1Text":"HeiGIT fournit la distance et la géométrie routières demandées, et non une distance à vol d'oiseau.","method2Title":"Examiner les prix","method2Text":"Le fichier contient des observations de prix non datées. Les stations sont situées approximativement par ville.","method3Title":"Éclairer la décision","method3Text":"L'optimiseur propose des achats et affiche leurs coûts, hypothèses et limites.","labHeading":"Que signifient 500 miles ?","labIntro":"Faites varier une distance hypothétique pour voir son effet sur la consommation et le minimum de ravitaillements.","labWarning":"Illustration arithmétique uniquement : ni itinéraire, ni stations vérifiées, ni achats optimisés.","distanceLabel":"Distance hypothétique","stopsLabel":"Pleins minimum","gallonsLabel":"Carburant consommé","distanceUnit":"miles","gallonsUnit":"gallons","closeHeading":"Tester un vrai trajet ?","closeText":"Choisissez deux villes américaines pour voir les routes, les arrêts et les coûts estimés.","closeCta":"Planifier","disclaimer":"Les prix proviennent d'observations non datées. Les marqueurs indiquent des villes approximatives, et non des pompes vérifiées.","footerLink":"Code source","pageTitle":"Fuel Route Optimizer | Itinéraires et carburant","journeyKicker":"AUTONOMIE / SCHÉMA ILLUSTRATIF","journeySvgTitle":"Un trajet schématique en cinq étapes de 100 miles. Il ne représente aucune route réelle.","journeyDisclaimer":"Schéma illustratif : ni véritable itinéraire ni station vérifiée.","journeyTank":"Réservoir initial","journeyEfficiency":"Consommation"},"pt":{"navLabel":"Navegação principal","homeLabel":"Página inicial do Fuel Route Optimizer","languageLabel":"Idioma","navMethod":"O método","navPlanner":"Planejador","headline":"A distância é só metade da história.","intro":"A outra metade é combustível. Explore rotas nos Estados Unidos, estime onde será preciso abastecer e entenda as premissas antes de viajar.","cta":"Abrir o planejador","secondary":"Conhecer o método","heroFoot":"Desenvolvido com Django, HeiGIT e OpenFreeMap","instrumentTitle":"Um tanque cheio. Até 500 milhas.","presetsLabel":"Distâncias de exemplo","methodHeading":"A estrada. Os preços. A decisão.","methodIntro":"O traçado real da rota é combinado com o arquivo de preços. O resultado distingue novas compras do valor do combustível inicial.","method1Title":"Seguir a estrada","method1Text":"O HeiGIT fornece distância e geometria rodoviárias, não uma aproximação em linha reta.","method2Title":"Considerar os preços","method2Text":"O arquivo contém observações de preços sem data. Os postos têm posições aproximadas por cidade.","method3Title":"Explicar o resultado","method3Text":"O otimizador sugere compras de combustível e apresenta custos, premissas e limitações.","labHeading":"O que significam 500 milhas?","labIntro":"Altere uma distância hipotética para entender o consumo e a quantidade mínima de abastecimentos.","labWarning":"Somente uma ilustração matemática: não é uma rota, não verifica postos e não otimiza compras.","distanceLabel":"Distância hipotética","stopsLabel":"Paradas mínimas","gallonsLabel":"Combustível consumido","distanceUnit":"milhas","gallonsUnit":"galões","closeHeading":"Vamos testar uma rota real?","closeText":"Escolha duas cidades dos Estados Unidos para ver a rota, as paradas e os custos estimados.","closeCta":"Planejar","disclaimer":"Os preços são observações sem data. Os marcadores são locais aproximados por cidade, não bombas de combustível verificadas.","footerLink":"Código-fonte","pageTitle":"Fuel Route Optimizer | Planejamento de rotas nos EUA","journeyKicker":"AUTONOMIA / TRAJETO ILUSTRATIVO","journeySvgTitle":"Um percurso esquemático com cinco intervalos de 100 milhas. Não representa uma estrada real.","journeyDisclaimer":"Ilustração apenas: não é uma rota real nem um posto verificado.","journeyTank":"Tanque inicial","journeyEfficiency":"Consumo"}};
  const langSelect=document.getElementById('language');
  const slider=document.getElementById('distanceSlider');
  const rangeVisual=document.getElementById('rangeSegments');
  const supported=Object.keys(translations);
  let language='en';
  try{
    const previous=localStorage.getItem('fuel-route-language-v2');
    if(supported.includes(previous))language=previous;
  }catch(_){}
  const formatNumber=(value)=>new Intl.NumberFormat(
    {en:'en-US',es:'es-AR',fr:'fr-FR',pt:'pt-BR'}[language],
    {maximumFractionDigits:1}
  ).format(value);
  function updateRange(){
    if(!slider||!rangeVisual)return;
    const distance=Number(slider.value);
    const refills=Math.max(0,Math.ceil(distance/500)-1);
    const usedGallons=distance/10;
    document.getElementById('distanceValue').textContent=formatNumber(distance);
    document.getElementById('refillValue').textContent=formatNumber(refills);
    document.getElementById('gallonsValue').textContent=formatNumber(usedGallons);
    document.querySelectorAll('[data-distance]').forEach(button=>{
      button.setAttribute('aria-pressed',String(Number(button.dataset.distance)===distance));
    });
    rangeVisual.replaceChildren();
    let remaining=distance;
    while(remaining>0){
      const piece=Math.min(remaining,500);
      const segment=document.createElement('span');
      segment.className='lab__segment';
      segment.style.flexGrow=String(piece);
      segment.style.flexBasis='0';
      rangeVisual.appendChild(segment);
      remaining-=piece;
    }
  }
  function apply(){
    document.documentElement.lang=language==='pt'?'pt-BR':language;
    langSelect.value=language;
    document.title=translations[language].pageTitle;
    document.querySelectorAll('[data-i18n]').forEach(element=>{
      const copy=translations[language][element.dataset.i18n];
      if(typeof copy==='string')element.textContent=copy;
    });
    document.querySelectorAll('[data-i18n-aria]').forEach(element=>{
      const copy=translations[language][element.dataset.i18nAria];
      if(typeof copy==='string')element.setAttribute('aria-label',copy);
    });
    updateRange();
    document.dispatchEvent(new Event('fuel:language-change'));
  }
  langSelect.addEventListener('change',event=>{
    if(!supported.includes(event.target.value))return;
    language=event.target.value;
    try{localStorage.setItem('fuel-route-language-v2',language);}catch(_){}
    apply();
  });
  slider?.addEventListener('input',updateRange);
  document.querySelectorAll('[data-distance]').forEach(button=>{
    button.addEventListener('click',()=>{
      if(!slider)return;
      slider.value=button.dataset.distance;
      updateRange();
    });
  });
  apply();
})();