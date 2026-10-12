// ===== Videos: every ID verified live through YouTube oEmbed (HTTP 200, real title + channel) on 2026-10-11 =====
const YT = {
  wave:   ['DSz4ZILAneQ','Wavelength, Frequency, Energy, Speed &amp; Amplitude Equations (The Organic Chemistry Tutor)'],
  spec:   ['KWQitt-kDFE','Electromagnetic Spectrum Explained (The Organic Chemistry Tutor)'],
  bohr:   ['mXxsT1ut35Q','Bohr Model of the Hydrogen Atom and Electron Transitions (The Organic Chemistry Tutor)'],
  dual:   ['XK2Y0D76S9U','de Broglie Equation &amp; Heisenberg Uncertainty Principle (Chad&#39;s Prep)'],
  qn:     ['lPptuKlCM6k','Quantum Numbers: n, l, ml, ms &amp; SPDF Orbitals (The Organic Chemistry Tutor)'],
  rules:  ['C6afrc1QS6Y','Aufbau, Hund&#39;s Rule &amp; Pauli Exclusion (The Organic Chemistry Tutor)'],
  exc:    ['Ur2PuzJ7KWs','Electron Configuration Exceptions: Chromium &amp; Copper (The Organic Chemistry Tutor)'],
  ions:   ['bmA20vMnbKM','Electron Configuration of Ions and Para/Diamagnetic Species (Rowdy Chemist Jr)'],
  trends: ['Gy9HR65DpYQ','Ionization Energy, Electron Affinity, Atomic and Ionic Radius, Metallic Character (The Organic Chemistry Tutor)'],
  bonds:  ['Ef9605V0wz8','Ionic, Covalent, and Metallic Bonding (Chad&#39;s Prep)'],
  polar:  ['tbrDv_cc_fE','Electronegativity and Chemical Bond Types (London Jenks)'],
  ionic:  ['US9XscmIfxE','Naming Binary Ionic Compounds With Transition Metals &amp; Polyatomic Ions (The Organic Chemistry Tutor)'],
  ionic2: ['Rq0A-AHdB74','Naming Ionic Compounds with Transition Metals (Tyler DeWitt)'],
  molec:  ['3agUL7-ezXk','How To Name Covalent Molecular Compounds (The Organic Chemistry Tutor)'],
};
// Topic-specific links first; anything else falls back to its chapter's video (applied right below).
const KHAN = {
  'Sep 16 lecture: the EM spectrum': YT.spec,
  'Sep 14 lecture: effect of EM radiation on matter': YT.spec,
  'Sep 28 lecture: exceptions': YT.exc,
  'Exam 2 study guide, topic 8c': YT.exc,
  'Oct 7 lecture: continuum of bond types': YT.polar,
  'Oct 7 lecture: electronegativity': YT.polar,
  'Oct 7 lecture: trends in electronegativity': YT.polar,
  'Oct 9 lecture: electron distribution in HCl': YT.polar,
  'Handout 12: naming molecular compounds': YT.molec,
  'Oct 9 lecture: naming binary molecular compounds': YT.molec,
  'Handout 12: prefixes': YT.molec,
};
const KHAN_CH = {light:YT.wave, bohr:YT.bohr, qm:YT.dual, qn:YT.qn, econf:YT.rules, ions:YT.ions, ptable:YT.trends, trends:YT.trends, bonds:YT.bonds, names:YT.ionic};
Q.forEach(q => { if (!q.khan && !KHAN[q.lec]) q.khan = KHAN_CH[q.chId]; });

const GLOSSARY = [
  {ch:'light',t:"Electromagnetic (EM) radiation",d:"Energy that travels as a wave of electric and magnetic fields; light in all its forms, all moving at c in a vacuum"},
  {ch:'light',t:"The 7 EM regions, low to high energy",d:"Radio, microwave, infrared, visible, ultraviolet, X-ray, gamma (RaMIVUXGam)"},
  {ch:'light',t:"Wavelength (&lambda;)",d:"Distance between two matching points on a wave (peak to peak); sets the color of visible light"},
  {ch:'light',t:"Frequency (&nu;)",d:"Number of wave cycles passing a point per second, in Hz (s<sup>-1</sup>)"},
  {ch:'light',t:"Amplitude",d:"Height of a wave; sets the brightness (intensity), not the color"},
  {ch:'light',t:"Speed of light, c",d:"3.00 &times; 10<sup>8</sup> m/s in a vacuum, the same for every type of EM radiation"},
  {ch:'light',t:"c = &lambda;&nu;",d:"Wavelength and frequency are inversely related: one goes up, the other goes down"},
  {ch:'light',t:"Photon",d:"A single particle (packet) of light with energy E = h&nu; = hc/&lambda;"},
  {ch:'light',t:"Planck's constant, h",d:"6.626 &times; 10<sup>-34</sup> J&middot;s; links a photon's energy to its frequency"},
  {ch:'light',t:"Visible light range",d:"About 400 nm (violet, highest energy) to 750 nm (red, lowest energy)"},
  {ch:'light',t:"Observed color",d:"The reflected or transmitted color; the absorbed color is its complement"},
  {ch:'light',t:"Infrared (IR) effect on molecules",d:"Makes bonds vibrate (microwaves make molecules rotate; UV and visible excite electrons)"},
  {ch:'bohr',t:"Emission spectrum",d:"A plot of the exact energies of light leaving a species after it is excited; lines, unique to each element"},
  {ch:'bohr',t:"Quantized",d:"Restricted to certain specific values, like the allowed energies of an electron in an atom"},
  {ch:'bohr',t:"Bohr model",d:"Hydrogen's electron moves only in certain orbits, each with a fixed (quantized) energy"},
  {ch:'bohr',t:"Excitation",d:"Electron absorbs energy and moves to a higher shell (n<sub>f</sub> &gt; n<sub>i</sub>)"},
  {ch:'bohr',t:"Emission",d:"Electron drops to a lower shell and releases the energy difference as a photon (n<sub>f</sub> &lt; n<sub>i</sub>)"},
  {ch:'bohr',t:"Rydberg equation",d:"1/&lambda;, &nu; or &Delta;E = R<sub>H</sub>(1/n<sub>f</sub><sup>2</sup> - 1/n<sub>i</sub><sup>2</sup>); positive answer = emitted, negative = absorbed"},
  {ch:'bohr',t:"Rydberg constants",d:"2.18 &times; 10<sup>-18</sup> J (energy), 1.097 &times; 10<sup>7</sup> m<sup>-1</sup> (1/wavelength), 3.290 &times; 10<sup>15</sup> s<sup>-1</sup> (frequency)"},
  {ch:'bohr',t:"Flame test",d:"Heating a salt makes its electrons emit a color unique to the element, like a fingerprint"},
  {ch:'qm',t:"Wave-particle duality",d:"Electrons (and light) behave as both particles and waves; shown by the double-slit experiment"},
  {ch:'qm',t:"de Broglie relation",d:"&lambda; = h/mv: all matter has a wavelength (not on the formula sheet)"},
  {ch:'qm',t:"Heisenberg uncertainty principle",d:"An electron's position and velocity cannot both be known precisely at once, so its position is a probability"},
  {ch:'qm',t:"Wavefunction (&psi;)",d:"Solution to Schr&ouml;dinger's equation; &psi; itself has no physical meaning, &psi;<sup>2</sup> is the probability of finding the electron"},
  {ch:'qm',t:"Atomic orbital",d:"A region of space in an atom where an electron can reside (the 'house' in his analogy)"},
  {ch:'qm',t:"Orbital surface plot",d:"The 3D shape enclosing where the electron is found 90% of the time"},
  {ch:'qn',t:"Principal quantum number (n)",d:"Shell: the size and energy of the orbital; n = 1, 2, 3, ... (the city)"},
  {ch:'qn',t:"Angular momentum quantum number (&#8467;)",d:"Subshell: the shape of the orbital; &#8467; = 0 to n - 1 (s, p, d, f) (the street)"},
  {ch:'qn',t:"Magnetic quantum number (m<sub>&#8467;</sub>)",d:"Orientation of the orbital; -&#8467; to +&#8467;, so 2&#8467; + 1 orbitals per subshell (the house number)"},
  {ch:'qn',t:"Spin quantum number (m<sub>s</sub>)",d:"Electron spin: +&frac12; (up) or -&frac12; (down)"},
  {ch:'qn',t:"Shell",d:"Layer of an atom that contains electrons, set by n; holds 2n<sup>2</sup> electrons (2, 8, 18, 32)"},
  {ch:'qn',t:"Subshell",d:"Part of a shell containing orbitals of the same shape, set by &#8467;"},
  {ch:'qn',t:"s orbital",d:"Sphere; 1 per subshell; found in every shell"},
  {ch:'qn',t:"p orbitals",d:"Dumbbells; 3 per subshell, at right angles (x, y, z), one nodal plane each; from n = 2 up"},
  {ch:'qn',t:"d orbitals",d:"Mostly cloverleaf (4 cloverleaves plus 1 p-like shape); 5 per subshell; from n = 3 up"},
  {ch:'qn',t:"f orbitals",d:"Complex shapes; 7 per subshell; from n = 4 up"},
  {ch:'econf',t:"Electron configuration",d:"A list of the occupied subshells and their electron counts, e.g. 1s<sup>2</sup>2s<sup>2</sup>2p<sup>3</sup>"},
  {ch:'econf',t:"Noble-gas (shortcut) configuration",d:"Configuration with the previous noble gas's core in brackets, e.g. [Ar]4s<sup>2</sup>"},
  {ch:'econf',t:"Orbital diagram",d:"Boxes (or lines) for each orbital with half-arrows for electrons, arranged by energy"},
  {ch:'econf',t:"Aufbau principle",d:"Electrons fill the lowest-energy orbitals first (1s, 2s, 2p, 3s, 3p, 4s, 3d, 4p ...)"},
  {ch:'econf',t:"Pauli exclusion principle",d:"No two electrons in an atom share all four quantum numbers: at most 2 per orbital, opposite spins"},
  {ch:'econf',t:"Hund's rule",d:"In a subshell, put one electron in each orbital with parallel spins before pairing any"},
  {ch:'econf',t:"Penetration",d:"Why 2s fills before 2p and 4s before 3d: s electrons get closer to the nucleus, so they are lower in energy"},
  {ch:'econf',t:"Configuration exceptions (d<sup>4</sup>, d<sup>9</sup>)",d:"Cr, Mo: d<sup>4</sup>s<sup>2</sup> becomes d<sup>5</sup>s<sup>1</sup>. Cu, Ag: d<sup>9</sup>s<sup>2</sup> becomes d<sup>10</sup>s<sup>1</sup>. Half-filled and filled subshells are favored"},
  {ch:'ions',t:"Isoelectronic",d:"Having the same total number of electrons (e.g. Na<sup>+</sup>, F<sup>-</sup> and Ne all have 10)"},
  {ch:'ions',t:"Ion formation goal",d:"Gain or lose electrons to match the nearest noble gas, because filled shells are lower in energy"},
  {ch:'ions',t:"Transition-metal ions",d:"Lose their outermost s electrons before any d electrons (Fe<sup>2+</sup> = [Ar]3d<sup>6</sup>)"},
  {ch:'ions',t:"Paramagnetic",d:"Has at least one unpaired electron; attracted to a magnetic field"},
  {ch:'ions',t:"Diamagnetic",d:"All electrons paired; slightly repelled by a magnetic field"},
  {ch:'ions',t:"Valence electrons",d:"Electrons in the outermost shell; for main-group elements, the group A number"},
  {ch:'ions',t:"Core electrons",d:"All electrons inside the valence shell (the noble-gas core plus any filled d or f subshells)"},
  {ch:'ptable',t:"Period / group",d:"Period = a row (7 of them); group = a column (18 of them)"},
  {ch:'ptable',t:"Periodic law",d:"Properties repeat in a regular way with atomic number, because the number of valence electrons repeats"},
  {ch:'ptable',t:"Metals",d:"Left side (94 of 118); form cations; good conductors; malleable, ductile; solid except Hg"},
  {ch:'ptable',t:"Nonmetals",d:"Right side (18 of 118); form anions; poor conductors; 11 gases, 1 liquid (Br<sub>2</sub>), 6 brittle solids"},
  {ch:'ptable',t:"Metalloids",d:"Along the staircase (B, Si, Ge, As, Sb, Te); shiny like metals, brittle like nonmetals, semiconductors"},
  {ch:'ptable',t:"Main group / transition / inner transition",d:"A groups (s and p blocks) / B groups (d block) / the two f-block rows"},
  {ch:'ptable',t:"Diatomic elements",d:"Br<sub>2</sub>, I<sub>2</sub>, N<sub>2</sub>, Cl<sub>2</sub>, H<sub>2</sub>, O<sub>2</sub>, F<sub>2</sub> (BrINClHOF)"},
  {ch:'trends',t:"Effective nuclear charge (Z<sub>eff</sub>)",d:"Net pull on a valence electron, Z<sub>eff</sub> = Z - S (S = shielding core electrons); rises across a period"},
  {ch:'trends',t:"Atomic radius trend",d:"Increases down a group (bigger outer orbital) and decreases across a period (Z<sub>eff</sub> rises)"},
  {ch:'trends',t:"Ionic radius",d:"Cations are smaller than their atoms (about half); anions are larger (about double)"},
  {ch:'trends',t:"Ionization energy (IE)",d:"Energy needed to remove one electron from a gaseous atom; decreases down a group, increases across a period"},
  {ch:'trends',t:"Successive ionization energies",d:"Each one is larger; a huge jump appears once a core electron is being removed"},
  {ch:'trends',t:"Electron affinity (EA)",d:"Energy change when a gaseous atom gains an electron; more negative across a period, no definite trend down a group"},
  {ch:'trends',t:"Metallic character",d:"How readily an element behaves as a metal (loses electrons); increases down a group and to the left"},
  {ch:'bonds',t:"Chemical bond",d:"An attraction that holds atoms or ions together"},
  {ch:'bonds',t:"Ionic bond",d:"Attraction between cations and anions after electrons are transferred (metal + nonmetal)"},
  {ch:'bonds',t:"Covalent bond",d:"Two atoms share valence electrons; the shared pair is attracted to both nuclei (nonmetals)"},
  {ch:'bonds',t:"Metallic bond",d:"Metal atoms in a 'sea' of electrons that float freely, which is why metals conduct"},
  {ch:'bonds',t:"Electronegativity (&chi;)",d:"How strongly an atom in a bond attracts the shared electrons; increases up and to the right, F highest (4.0)"},
  {ch:'bonds',t:"NClOF values",d:"N 3.0, Cl 3.0, O 3.5, F 4.0: the four most electronegative atoms (memorize)"},
  {ch:'bonds',t:"Nonpolar (pure) covalent bond",d:"&Delta;&chi; from 0 to 0.4; electrons shared equally"},
  {ch:'bonds',t:"Polar covalent bond",d:"&Delta;&chi; from 0.4 to 2.0; electrons shared unequally, giving &delta;+ and &delta;- ends"},
  {ch:'bonds',t:"Ionic bond (by &Delta;&chi;)",d:"&Delta;&chi; above 2.0; electrons transferred"},
  {ch:'bonds',t:"Molecule",d:"Two or more atoms joined by covalent bonds (H<sub>2</sub>, H<sub>2</sub>O)"},
  {ch:'bonds',t:"Compound",d:"A substance made of two or more different elements, either ionic (NaCl) or molecular (glucose)"},
  {ch:'bonds',t:"Polyatomic ion",d:"An ion made of two or more covalently bonded atoms, e.g. NO<sub>3</sub><sup>-</sup>"},
  {ch:'names',t:"Naming a main-group cation",d:"Element name + 'ion' (Na<sup>+</sup> = sodium ion); groups 1A, 2A, 3A need no Roman numeral"},
  {ch:'names',t:"Naming a transition-metal cation",d:"Element name + charge in Roman numerals: Cr<sup>3+</sup> = chromium(III) ion"},
  {ch:'names',t:"-ous / -ic",d:"Older names: -ous = lower charge (ferrous Fe<sup>2+</sup>), -ic = higher charge (ferric Fe<sup>3+</sup>)"},
  {ch:'names',t:"Naming a monatomic anion",d:"Replace the ending with -ide: chloride, oxide, nitride, phosphide, sulfide, carbide"},
  {ch:'names',t:"-ate / -ite",d:"-ate has more oxygens than -ite (nitrate NO<sub>3</sub><sup>-</sup>, nitrite NO<sub>2</sub><sup>-</sup>)"},
  {ch:'names',t:"per- / hypo-",d:"per- = most oxygens (perchlorate ClO<sub>4</sub><sup>-</sup>), hypo- = fewest (hypochlorite ClO<sup>-</sup>)"},
  {ch:'names',t:"Oxyanion",d:"A polyatomic anion of oxygen and another nonmetal"},
  {ch:'names',t:"Ammonium",d:"NH<sub>4</sub><sup>+</sup>"},
  {ch:'names',t:"Hydronium",d:"H<sub>3</sub>O<sup>+</sup>"},
  {ch:'names',t:"Acetate",d:"C<sub>2</sub>H<sub>3</sub>O<sub>2</sub><sup>-</sup>"},
  {ch:'names',t:"Carbonate",d:"CO<sub>3</sub><sup>2-</sup>"},
  {ch:'names',t:"Chlorate",d:"ClO<sub>3</sub><sup>-</sup>"},
  {ch:'names',t:"Hydroxide",d:"OH<sup>-</sup>"},
  {ch:'names',t:"Nitrate",d:"NO<sub>3</sub><sup>-</sup>"},
  {ch:'names',t:"Phosphate",d:"PO<sub>4</sub><sup>3-</sup>"},
  {ch:'names',t:"Sulfate",d:"SO<sub>4</sub><sup>2-</sup>"},
  {ch:'names',t:"Prefixes 1 to 10",d:"mono, di, tri, tetra, penta, hexa, hepta, octa, nona, deca"},
  {ch:'names',t:"Binary molecular naming",d:"(prefix)(first element) (prefix)(second element, -ide); never mono- on the first element"},
  {ch:'names',t:"Binary ionic naming",d:"Cation name, then anion name; no prefixes; charges must sum to zero"},
];

const CHAPTERS = [
  {id:'light', short:'Light'}, {id:'bohr', short:'Bohr + Rydberg'}, {id:'qm', short:'Wave-Particle'},
  {id:'qn', short:'Quantum Numbers'}, {id:'econf', short:'Configurations'}, {id:'ions', short:'Ions + Magnetism'},
  {id:'ptable', short:'Table Layout'}, {id:'trends', short:'Trends'}, {id:'bonds', short:'Bonds + Polarity'},
  {id:'names', short:'Naming'},
];
const SHORT = Object.fromEntries(CHAPTERS.map(c=>[c.id,c.short]));

const VIDEOS = [
  {ch:'Light and the EM spectrum', items:[[YT.wave[0],'Wavelength, Frequency, Energy, Speed &amp; Amplitude','The Organic Chemistry Tutor'],[YT.spec[0],'Electromagnetic Spectrum Explained','The Organic Chemistry Tutor']]},
  {ch:'Bohr model and the Rydberg equation', items:[[YT.bohr[0],'Bohr Model of the Hydrogen Atom, Electron Transitions, Lyman &amp; Balmer Series','The Organic Chemistry Tutor']]},
  {ch:'Wave-particle duality', items:[[YT.dual[0],'de Broglie Equation &amp; Heisenberg Uncertainty Principle','Chad&#39;s Prep']]},
  {ch:'Quantum numbers and orbitals', items:[[YT.qn[0],'Quantum Numbers: n, l, ml, ms &amp; SPDF Orbitals','The Organic Chemistry Tutor']]},
  {ch:'Electron configurations', items:[[YT.rules[0],'Aufbau&#39;s Principle, Hund&#39;s Rule &amp; Pauli&#39;s Exclusion Principle','The Organic Chemistry Tutor'],[YT.exc[0],'Electron Configuration Exceptions: Chromium &amp; Copper','The Organic Chemistry Tutor']]},
  {ch:'Ions and magnetism', items:[[YT.ions[0],'Electron Configuration of Ions and Paramagnetic/Diamagnetic Species','Rowdy Chemist Jr']]},
  {ch:'Periodic trends', items:[[YT.trends[0],'Ionization Energy, Electron Affinity, Atomic Radius, Ionic Radii, Electronegativity, Metal Character','The Organic Chemistry Tutor']]},
  {ch:'Bonds and polarity', items:[[YT.bonds[0],'Ionic, Covalent, and Metallic Bonding','Chad&#39;s Prep'],[YT.polar[0],'Electronegativity and Chemical Bond Types','London Jenks']]},
  {ch:'Naming compounds', items:[[YT.ionic[0],'Naming Binary Ionic Compounds With Transition Metals &amp; Polyatomic Ions','The Organic Chemistry Tutor'],[YT.ionic2[0],'Naming Ionic Compounds with Transition Metals Introduction','Tyler DeWitt'],[YT.molec[0],'How To Name Covalent Molecular Compounds','The Organic Chemistry Tutor']]},
];

// ===== Review guide: one section per chapter chip, in study-guide topic order =====
const GUIDE = [
{ch:'light', title:'Light and the electromagnetic spectrum', topics:'Study guide topics 1 to 3', html:`
<p>All EM radiation moves at <b>c = 3.00 &times; 10<sup>8</sup> m/s</b> in a vacuum. What changes from region to region is wavelength, frequency and energy, and they are locked together:</p>
<div class="math-block">c = &lambda;&nu; &nbsp;&nbsp; E = h&nu; &nbsp;&nbsp; E = hc/&lambda;<br>long &lambda;, low &nu;, low E &nbsp;&nbsp; short &lambda;, high &nu;, high E</div>
<div class="g-memo"><div class="g-memo-h">Memorize: the 7 regions, low to high energy</div><p><b>Radio, Microwave, Infrared, Visible, Ultraviolet, X-ray, Gamma</b> (RaMIVUXGam). Visible runs 400 nm (violet, high E) to 750 nm (red, low E): ROYGBV goes up in energy.</p></div>
<ul>
<li><b>Amplitude</b> sets brightness. <b>Wavelength</b> sets color.</li>
<li>What each region does to matter (his list): X-ray finds electron clouds; UV and visible excite electrons; IR makes bonds vibrate; microwaves rotate molecules; radio excites nuclei (NMR).</li>
<li>Observed color is the reflected or transmitted color. The absorbed color is its complement, and that energy goes into the electrons.</li>
<li>Energy is per photon. For N photons, multiply. For a mole, multiply by 6.022 &times; 10<sup>23</sup>.</li>
</ul>
<div class="g-ex"><div class="g-ex-h">Worked: Handout 7 #2</div><div class="math-block">Know: &lambda; = 400. nm, h, c &nbsp;&nbsp; Want: E (J)<br>Step 1, match units: 400. nm &times; (1 m / 10<sup>9</sup> nm) = 4.00 &times; 10<sup>-7</sup> m<br>Step 2: E = (6.626 &times; 10<sup>-34</sup>)(3.00 &times; 10<sup>8</sup>) / (4.00 &times; 10<sup>-7</sup>) = 4.97 &times; 10<sup>-19</sup> J (3 SF)</div></div>
<p class="g-trap"><b>Traps:</b> leaving nm or MHz unconverted (always get to m and s<sup>-1</sup>); using E = h&nu; when you were given &lambda;; stopping at one photon when the question asks for two.</p>`},
{ch:'bohr', title:'Emission spectra, the Bohr model and Rydberg', topics:'Study guide topics 4 and 5', html:`
<p>An excited atom releases energy as light, but only at <b>specific</b> energies. That line pattern is its <b>emission spectrum</b>, unique to each element, like a fingerprint (flame tests). Lines instead of a rainbow mean the electron's energies are <b>quantized</b>.</p>
<ul>
<li><b>Bohr model:</b> hydrogen's electron is allowed only in certain orbits, each with a fixed energy. Energy increases outward, and the levels crowd closer together as n grows.</li>
<li><b>Excitation:</b> absorb energy, n goes up (n<sub>f</sub> &gt; n<sub>i</sub>). <b>Emission:</b> release a photon, n goes down (n<sub>f</sub> &lt; n<sub>i</sub>).</li>
</ul>
<div class="math-block">1/&lambda; = R<sub>H</sub>(1/n<sub>f</sub><sup>2</sup> - 1/n<sub>i</sub><sup>2</sup>) &nbsp; R<sub>H</sub> = 1.097 &times; 10<sup>7</sup> m<sup>-1</sup><br>&nu; = R<sub>H</sub>(1/n<sub>f</sub><sup>2</sup> - 1/n<sub>i</sub><sup>2</sup>) &nbsp;&nbsp;&nbsp;&nbsp; R<sub>H</sub> = 3.290 &times; 10<sup>15</sup> s<sup>-1</sup><br>&Delta;E = R<sub>H</sub>(1/n<sub>f</sub><sup>2</sup> - 1/n<sub>i</sub><sup>2</sup>) &nbsp;&nbsp; R<sub>H</sub> = 2.18 &times; 10<sup>-18</sup> J</div>
<p><b>His sign rule:</b> a positive answer means energy was <b>emitted</b> as a photon; negative means <b>absorbed</b>. (OpenStax and Knewton often give &Delta;E of the atom instead, negative for emission. On his exam, use his rule.) Pick the R<sub>H</sub> whose units match what you want, and convert the given value into those units first.</p>
<div class="g-ex"><div class="g-ex-h">Worked: solving for a shell (Handout 7 #4)</div><div class="math-block">Know: &nu; = 6.16 &times; 10<sup>14</sup> Hz, n<sub>f</sub> = 2 &nbsp;&nbsp; Want: n<sub>i</sub><br>&nu;/R<sub>H</sub> = 1/n<sub>f</sub><sup>2</sup> - 1/n<sub>i</sub><sup>2</sup> &rarr; 1/n<sub>i</sub><sup>2</sup> = 1/4 - 0.1872 = 0.0628<br>n<sub>i</sub><sup>2</sup> = 15.9 &rarr; n<sub>i</sub> = 3.99 &rarr; n<sub>i</sub> = 4 (shells are whole numbers)</div></div>
<p class="g-trap"><b>Traps:</b> forgetting the last 1/x when solving for &lambda;; forgetting the square root (or inverting) when solving for n; mixing up which shell is n<sub>i</sub> and which is n<sub>f</sub>.</p>`},
{ch:'qm', title:'Wave-particle duality', topics:'Study guide topic 6', html:`
<ul>
<li><b>Double-slit experiment:</b> electrons made an interference pattern, like a wave. So the electron has both particle and wave properties.</li>
<li><b>de Broglie (1924):</b> <b>&lambda; = h/mv</b>. All matter has a wavelength. Big mass or high speed gives a tiny wavelength, which is why a baseball's (about 10<sup>-34</sup> m) never shows. <b>This equation is not on the formula sheet.</b></li>
<li><b>Schr&ouml;dinger (1926):</b> H&psi; = E&psi; treats the electron as a wave. &psi; itself means nothing physical; <b>&psi;<sup>2</sup> is the probability</b> of finding the electron, which is what an orbital is.</li>
<li><b>Heisenberg (1927):</b> position and velocity cannot both be known precisely at once. If we know the electron's energy, its position can only be a probability.</li>
<li>An <b>orbital surface plot</b> encloses where the electron is found 90% of the time.</li>
</ul>`},
{ch:'qn', title:'Quantum numbers and orbitals', topics:'Study guide topic 7', html:`
<table class="g-tbl"><thead><tr><th>Number</th><th>Values</th><th>Tells you</th><th>Analogy</th></tr></thead><tbody>
<tr><td>n (principal)</td><td>1, 2, 3, ...</td><td>shell: size and energy</td><td>city</td></tr>
<tr><td>&#8467; (angular momentum)</td><td>0 to n - 1</td><td>subshell: shape (0 s, 1 p, 2 d, 3 f)</td><td>street</td></tr>
<tr><td>m<sub>&#8467;</sub> (magnetic)</td><td>-&#8467; to +&#8467;</td><td>orientation; 2&#8467; + 1 orbitals</td><td>house number</td></tr>
<tr><td>m<sub>s</sub> (spin)</td><td>+&frac12;, -&frac12;</td><td>spin up or down</td><td></td></tr>
</tbody></table>
<table class="g-tbl"><thead><tr><th>Subshell</th><th>Shape</th><th>Orbitals</th><th>Max e<sup>-</sup></th><th>First shell</th></tr></thead><tbody>
<tr><td>s</td><td>sphere</td><td>1</td><td>2</td><td>n = 1</td></tr>
<tr><td>p</td><td>dumbbell, 3 at right angles</td><td>3</td><td>6</td><td>n = 2</td></tr>
<tr><td>d</td><td>cloverleaf (mostly)</td><td>5</td><td>10</td><td>n = 3</td></tr>
<tr><td>f</td><td>complex</td><td>7</td><td>14</td><td>n = 4</td></tr>
</tbody></table>
<p><b>Does the orbital exist?</b> Read (n, &#8467;, m<sub>&#8467;</sub>) left to right and check each number against the one before it. (1, 1, 0) fails at &#8467;: there is no 1p. (4, 3, 5) fails at m<sub>&#8467;</sub>. (5, 2, 1) is a 5d.</p>
<p>A shell holds <b>n<sup>2</sup> orbitals</b> and <b>2n<sup>2</sup> electrons</b>: 2, 8, 18, 32. The 4th shell has 16 orbitals (4s, 4p, 4d, 4f).</p>`},
{ch:'econf', title:'Electron configurations and orbital diagrams', topics:'Study guide topics 8 and 10', html:`
<p><b>Filling order:</b> 1s, 2s, 2p, 3s, 3p, <b>4s, 3d</b>, 4p, 5s, 4d, 5p, 6s ... Read it off the table: the s block, p block and d block are the subshells being filled, and the d block lags one shell behind (row 4 fills 3d).</p>
<ul>
<li><b>Aufbau:</b> lowest energy first. <b>Pauli:</b> at most 2 electrons per orbital, opposite spins. <b>Hund:</b> one per orbital, same spin, before pairing.</li>
<li><b>Why 4s before 3d:</b> penetration makes 4s lower in energy than 3d.</li>
<li><b>Full vs noble-gas notation:</b> Ca = 1s<sup>2</sup>2s<sup>2</sup>2p<sup>6</sup>3s<sup>2</sup>3p<sup>6</sup>4s<sup>2</sup> = [Ar]4s<sup>2</sup>. Knewton wants the filling order ([Ar]4s<sup>2</sup>3d<sup>5</sup>); his slides also write [Ar]3d<sup>5</sup>4s<sup>2</sup>. Same configuration.</li>
<li><b>Reading an element off its configuration:</b> the last term names it. 3p<sup>5</sup> = row 3, p block, 5th element = Cl.</li>
</ul>
<div class="g-memo"><div class="g-memo-h">Memorize: the d<sup>4</sup> and d<sup>9</sup> exceptions</div><p>One s electron moves into the d to reach a half-filled or filled d subshell. <b>Cr = [Ar]3d<sup>5</sup>4s<sup>1</sup></b> (not 3d<sup>4</sup>4s<sup>2</sup>), Mo the same pattern. <b>Cu = [Ar]3d<sup>10</sup>4s<sup>1</sup></b>, <b>Ag = [Kr]4d<sup>10</sup>5s<sup>1</sup></b>.</p></div>
<div class="g-ex"><div class="g-ex-h">Worked: oxygen's orbital diagram</div>${OB([['1s','ud'],['2s','ud'],['2p','ud u u']])}<p>8 electrons. Fill 1s and 2s, then spread the four 2p electrons by Hund's rule: two paired, two single. 2 unpaired, so O is paramagnetic.</p></div>
<p class="g-trap"><b>Traps:</b> skipping the 3d<sup>10</sup> in Ge, As, Se and Br; writing Cr or Cu the "regular" way; putting two same-spin arrows in one box.</p>`},
{ch:'ions', title:'Ions, magnetism, core and valence electrons', topics:'Study guide topics 9, 11 and 12', html:`
<p><b>Why ions form (Video 1):</b> to become <b>isoelectronic with the nearest noble gas</b>, because filled shells are lower in energy. Nonmetals fill their shell (gain electrons); metals empty theirs (lose electrons).</p>
<ul>
<li><b>Main-group charges:</b> 1A +1, 2A +2, 3A +3, 5A -3, 6A -2, 7A -1. Predict them straight from the configuration: [Ne]3s<sup>2</sup> loses 2 (Mg<sup>2+</sup>); [Ne]3s<sup>2</sup>3p<sup>4</sup> gains 2 (S<sup>2-</sup>).</li>
<li><b>Transition-metal ions lose the outer s electrons first</b>, even though s filled first. Fe = [Ar]3d<sup>6</sup>4s<sup>2</sup>, Fe<sup>2+</sup> = [Ar]3d<sup>6</sup>, Fe<sup>3+</sup> = [Ar]3d<sup>5</sup>. Cr<sup>+</sup> = [Ar]3d<sup>5</sup>.</li>
<li><b>p-block metals</b> lose p, then s, from the outer shell: Sn<sup>4+</sup> = [Kr]4d<sup>10</sup>.</li>
</ul>
<div class="g-memo"><div class="g-memo-h">Magnetism, decided from the orbital diagram</div><p><b>Paramagnetic:</b> at least one unpaired electron; attracted to a magnet. <b>Diamagnetic:</b> every electron paired; slightly repelled. Example: of V, V<sup>+</sup>, V<sup>2+</sup>, V<sup>3+</sup>, V<sup>4+</sup> and V<sup>5+</sup>, only V<sup>5+</sup> = [Ar] is diamagnetic.</p></div>
<p><b>Valence electrons</b> are those in the outermost shell, equal to the group A number for main-group elements (Se: 4s<sup>2</sup>4p<sup>4</sup> = 6). <b>Core electrons</b> are everything else, including filled d subshells: Ga has 3 valence and 28 core.</p>`},
{ch:'ptable', title:'Organization of the periodic table', topics:'Study guide topic 13', html:`
<ul>
<li><b>7 periods (rows), 18 groups (columns).</b> Same group = same number of valence electrons = similar properties. That repetition is the <b>periodic law</b>.</li>
<li><b>Blocks:</b> s (2 columns), p (6), d (10), f (14). The widths are the electron capacities of one s, three p, five d and seven f orbitals.</li>
<li><b>Main group</b> = A groups; <b>transition metals</b> = B groups (d block); <b>inner transition metals</b> = the two f-block rows. Group names: 1A alkali metals, 2A alkaline earth metals, 7A halogens, 8A noble gases.</li>
</ul>
<table class="g-tbl"><thead><tr><th></th><th>Where</th><th>Properties</th></tr></thead><tbody>
<tr><td>Metals (94)</td><td>left and center</td><td>form cations; good conductors; malleable, ductile; solid except Hg</td></tr>
<tr><td>Nonmetals (18)</td><td>upper right</td><td>form anions; poor conductors; 11 gases, Br<sub>2</sub> liquid, 6 brittle solids</td></tr>
<tr><td>Metalloids</td><td>the staircase: B, Si, Ge, As, Sb, Te</td><td>shiny like metals, brittle like nonmetals, semiconductors</td></tr>
</tbody></table>
<p><b>Diatomic elements:</b> Br<sub>2</sub>, I<sub>2</sub>, N<sub>2</sub>, Cl<sub>2</sub>, H<sub>2</sub>, O<sub>2</sub>, F<sub>2</sub>. <b>Polyatomic elements:</b> P<sub>4</sub>, S<sub>8</sub>.</p>`},
{ch:'trends', title:'Periodic trends', topics:'Study guide topic 14', html:`
<table class="g-tbl"><thead><tr><th>Property</th><th>Down a group</th><th>Across a period</th></tr></thead><tbody>
<tr><td>Atomic radius</td><td>increases</td><td>decreases</td></tr>
<tr><td>First ionization energy</td><td>decreases</td><td>increases</td></tr>
<tr><td>Electron affinity</td><td>no definite trend</td><td>more negative</td></tr>
<tr><td>Metallic character</td><td>increases</td><td>decreases</td></tr>
<tr><td>Electronegativity</td><td>decreases</td><td>increases</td></tr>
</tbody></table>
<p><b>Why, in his words:</b> down a group the outermost occupied orbital is bigger and farther from the nucleus; across a period the effective nuclear charge rises and pulls the same shell in. Metallic character runs opposite to ionization energy. Electronegativity tops out at F (4.0) and bottoms out at Fr (0.7).</p>
<p>One picture covers most of it: <b>size and metallic character grow toward the bottom left; ionization energy and electronegativity grow toward the top right.</b> Electron affinity gets more negative across a period but has no clean trend down a group.</p>
<ul>
<li><b>Z<sub>eff</sub> = Z - S</b> (on the formula sheet). Na valence: 11 - 10 = +1. Cl valence: 17 - 10 = +7.</li>
<li><b>Ions:</b> cations are smaller than their atoms (about half the radius); anions are larger (about double). In an isoelectronic series, more protons means smaller: Ca<sup>2+</sup> &lt; K<sup>+</sup> &lt; Cl<sup>-</sup> &lt; S<sup>2-</sup>.</li>
<li><b>Two dips in first IE</b> (his Video 2 chart): B is lower than Be (801 vs 899) because B's electron sits alone in a higher 2p; O is lower than N (1314 vs 1402) because O's fourth 2p electron is paired and repelled.</li>
<li><b>Successive IE:</b> each is larger, and there is a huge jump once you reach a core electron. IE<sub>2</sub> of K &gt; IE<sub>2</sub> of Ca; IE<sub>3</sub> of Be &gt; IE<sub>3</sub> of B.</li>
<li><b>Ionization energy</b> = energy to remove one electron from a gaseous atom. <b>Electron affinity</b> = energy change on adding one; more negative means a stronger pull (Cl -349 kJ/mol is the most negative).</li>
</ul>`},
{ch:'bonds', title:'Bonds, electronegativity and polarity', topics:'Study guide topics 15 to 19', html:`
<table class="g-tbl"><thead><tr><th>Bond</th><th>What happens</th><th>Between</th></tr></thead><tbody>
<tr><td>Ionic</td><td>electrons transferred; cations and anions attract</td><td>metal + nonmetal</td></tr>
<tr><td>Covalent</td><td>valence electrons shared; the pair is pulled by both nuclei</td><td>nonmetals</td></tr>
<tr><td>Metallic</td><td>a "sea" of electrons around metal atoms</td><td>metals</td></tr>
</tbody></table>
<div class="g-memo"><div class="g-memo-h">Memorize: NClOF</div><p><b>N 3.0, Cl 3.0, O 3.5, F 4.0.</b> Electronegativity rises up a group and left to right. Other values will be given in the question.</p></div>
<div class="math-block">&Delta;&chi; = larger &chi; - smaller &chi;<br>0 to 0.4 &rarr; nonpolar covalent (shared equally)<br>0.4 to 2.0 &rarr; polar covalent (shared unequally, &delta;+ and &delta;-)<br>above 2.0 &rarr; ionic (transferred)</div>
<ul>
<li>The more electronegative atom gets the &delta;- end: in H-Cl, Cl is &delta;-.</li>
<li><b>Most polar</b> = biggest &Delta;&chi;. <b>Strongest</b> is a different question: double and triple bonds beat single bonds (his key: C=N is strongest, H-F is most polar).</li>
<li><b>E &prop; q<sub>1</sub>q<sub>2</sub>/r:</b> bigger charges and smaller ions attract harder (MgO beats NaCl).</li>
<li><b>Two tools, two jobs:</b> for a whole compound, metal + nonmetal = ionic (how his key decides the ionic/covalent column); the &Delta;&chi; continuum classifies a single bond when &chi; values are given.</li>
<li>Pb and Sn are metals even though they sit in the p block, so PbS<sub>2</sub> is ionic. Na<sub>2</sub>SO<sub>4</sub> and Ca(OH)<sub>2</sub> contain <b>both</b> bond types.</li>
<li><b>Element vs compound:</b> He (atomic element), H<sub>2</sub> and P<sub>4</sub> (molecular elements), NaCl (ionic compound), glucose (molecular compound). A polyatomic ion is a charged group of covalently bonded atoms (NO<sub>3</sub><sup>-</sup>); a monatomic ion is one atom (Cl<sup>-</sup>).</li>
</ul>`},
{ch:'names', title:'Naming ions and binary compounds', topics:'Study guide topics 19 to 21', html:`
<div class="g-memo"><div class="g-memo-h">Memorize: nine polyatomic ions (formula and charge)</div>
<table class="g-tbl g-tbl-tight"><tbody>
<tr><td>ammonium</td><td>NH<sub>4</sub><sup>+</sup></td><td>hydroxide</td><td>OH<sup>-</sup></td></tr>
<tr><td>hydronium</td><td>H<sub>3</sub>O<sup>+</sup></td><td>nitrate</td><td>NO<sub>3</sub><sup>-</sup></td></tr>
<tr><td>acetate</td><td>C<sub>2</sub>H<sub>3</sub>O<sub>2</sub><sup>-</sup></td><td>phosphate</td><td>PO<sub>4</sub><sup>3-</sup></td></tr>
<tr><td>carbonate</td><td>CO<sub>3</sub><sup>2-</sup></td><td>sulfate</td><td>SO<sub>4</sub><sup>2-</sup></td></tr>
<tr><td>chlorate</td><td>ClO<sub>3</sub><sup>-</sup></td><td></td><td></td></tr>
</tbody></table></div>
<p><b>Ions.</b> Main-group cation: element + "ion" (sodium ion). Transition-metal cation: Roman numeral for the charge (chromium(III) ion); older names use -ous for the lower charge and -ic for the higher (ferrous Fe<sup>2+</sup>, ferric Fe<sup>3+</sup>). Monatomic anion: -ide (chloride, oxide, nitride, phosphide, sulfide, carbide). Oxyanions: -ate has more oxygens than -ite; per- has the most and hypo- the fewest (ClO<sup>-</sup>, ClO<sub>2</sub><sup>-</sup>, ClO<sub>3</sub><sup>-</sup>, ClO<sub>4</sub><sup>-</sup>).</p>
<p><b>Binary ionic compounds</b> (metal + nonmetal): cation name, then anion name, <b>no prefixes</b>. Charges must sum to zero; find a transition metal's charge from the anions. Example: Co<sub>2</sub>S<sub>3</sub>: 3 &times; (-2) = -6, so each Co is +3, cobalt(III) sulfide. More than one polyatomic ion takes parentheses: (NH<sub>4</sub>)<sub>2</sub>CO<sub>3</sub>.</p>
<p><b>Hydrates</b> are ionic compounds with water attached: CoCl<sub>2</sub>&middot;6H<sub>2</sub>O is cobalt(II) chloride hexahydrate. <b>Zn, Ag and Cd</b> form only one ion each (Zn<sup>2+</sup>, Ag<sup>+</sup>, Cd<sup>2+</sup>), so the textbook usually drops their numeral (zinc oxide, silver chloride). His handout says to show a transition metal's charge, so if one shows up, ask him which he wants.</p>
<p><b>Binary molecular compounds</b> (two nonmetals): prefixes give the counts, and <b>mono- is never used on the first element</b>. Drop the a or o before "oxide": pentoxide, monoxide, tetroxide. Examples: PCl<sub>5</sub> phosphorus pentachloride, N<sub>2</sub>O<sub>4</sub> dinitrogen tetroxide, CO carbon monoxide.</p>
<div class="g-memo"><div class="g-memo-h">Memorize: prefixes 1 to 10</div><p>mono, di, tri, tetra, penta, hexa, hepta, octa, nona, deca</p></div>
<p class="g-trap"><b>Two things on his Handout 12 to double-check:</b> the table prints permanganate as MnO<sub>4</sub><sup>2-</sup>, but the standard formula is MnO<sub>4</sub><sup>-</sup> (MnO<sub>4</sub><sup>2-</sup> is manganate). It is not on the memorize list. His Chapter 4 key also spells "diphosphorous"; the element is phosphorus.</p>`},
];
