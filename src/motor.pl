:- dynamic hecho_confirmado/3.
:- dynamic hallazgo_registrado/3.
:- dynamic estructura_detectada/3.

% --- MOTOR DE INFERENCIA ARQUEOLOGICA (HUELVA) - VERSIÓN DE ALTA PRECISIÓN ---

% 1. YACIMIENTOS DE REFERENCIA
yacimiento('Dolmen de Soto', 37.35, -6.82, 'arcilloso', 'Prehistoria').
yacimiento('Cista de Niebla', 37.36, -6.68, 'calizo', 'Bronce').
yacimiento('Villa de San Walabonso', 37.39, -6.85, 'ferruginoso', 'Romana').

% 2. GEOLOGIA Y PREFERENCIAS
terreno(37.30, 37.45, -6.90, -6.70, 'arcilloso').
preferencia('Romana', 'arcilloso').
preferencia('Prehistoria', 'calizo').

% 3. REGLAS DE ALTA PRIORIDAD (BASADAS EN EVIDENCIA REAL)
interpretar(P, A, 'Muy Alta', 'Asentamiento Romano', 'EVIDENCIA DIRECTA: Tegulas/Muros confirmados en este sector.') :-
    hallazgo_registrado(P, A, Tipo),
    (Tipo = 'tegula_ladrillo'; Tipo = 'Estructura/Muro'), !.

interpretar(P, A, 'Alta', 'Zona de Actividad', 'EVIDENCIA DIRECTA: Moneda o material mueble registrado.') :-
    hallazgo_registrado(P, A, 'Moneda'), !.

% 4. DETECCION DE ESTRUCTURAS (FILTRO RESTRICTIVO)
% Hemos estrechado el rango de pendiente para evitar falsos positivos por erosión natural.
interpretar(P, A, 'Alta', 'Cimentacion Enterrada', 'ANOMALÍA TÉCNICA: Pendiente artificial compatible con cimientos enterrados en zona de terraza.') :-
    P > 18, P < 32,      % Rango mucho más estricto (antes era 12-35)
    A > 25, A < 110,     % Acotamos altitud para evitar zonas de inundación y cumbres altas
    preferencia('Romana', 'arcilloso'), !.

% 5. REGLAS DE ANALOGÍA (APRENDIZAJE ESTRICTO)
% Solo dispara si el relieve es prácticamente idéntico al hallazgo previo.
interpretar(P, _, 'Media-Alta', 'Sugerida por Analogia', 'SIMILITUD GEOMÉTRICA: Perfil de relieve casi idéntico a hallazgo de moneda previo.') :-
    hallazgo_registrado(P_ant, _, 'Moneda'),
    abs(P - P_ant) < 0.1, !. % Tolerancia mínima (antes 0.3) para máxima precisión.

% 6. PATRONES DE INGENIERÍA (BARRIDO GENERAL)
interpretar(P, A, Prob, Epoca, Explicacion) :-
    (
        % Villa Romana (Muy restrictivo: llano casi perfecto)
        (P < 2.5, A > 15, A < 85, preferencia('Romana', 'arcilloso')) -> 
        (Prob = 'Alta', Epoca = 'Romana', Explicacion = 'Terreno óptimo para Villa: Llanura arcillosa fértil y nivelada.');
        
        % Camino/Calzada (Pendiente constante y controlada)
        (P >= 3.5, P < 5.5, A < 130) -> 
        (Prob = 'Media', Epoca = 'Romana/Vial', Explicacion = 'Pendiente constante: Compatible con trazados de ingeniería civil.');
        
        % Patron Prehistorico (Control visual en lomas)
        (P >= 8, P < 11, A > 50) -> 
        (Prob = 'Media-Alta', Epoca = 'Prehistoria', Explicacion = 'Posición estratégica: Loma con dominio visual del entorno.');
        
        % Caso por defecto (Restrictivo: probabilidad baja)
        (Prob = 'Muy Baja', Epoca = 'Ninguna', Explicacion = 'Relieve compatible con formación geológica natural estándar.')
    ).

% Predicados de seguridad
hallazgo_registrado(-1, -1, 'ninguno').
hecho_confirmado(-1, -1, 'no').