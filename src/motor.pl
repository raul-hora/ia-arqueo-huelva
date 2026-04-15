:- dynamic hecho_confirmado/3.
:- dynamic hallazgo_registrado/3.
:- dynamic estructura_detectada/3.

% --- MOTOR DE INFERENCIA ARQUEOLOGICA (HUELVA) ---

% 1. YACIMIENTOS DE REFERENCIA (Conocimiento Base)
yacimiento('Dolmen de Soto', 37.35, -6.82, 'arcilloso', 'Prehistoria').
yacimiento('Cista de Niebla', 37.36, -6.68, 'calizo', 'Bronce').
yacimiento('Villa de San Walabonso', 37.39, -6.85, 'ferruginoso', 'Romana').

% 2. GEOLOGIA Y PREFERENCIAS
terreno(37.30, 37.45, -6.90, -6.70, 'arcilloso').
preferencia('Romana', 'arcilloso').
preferencia('Prehistoria', 'calizo').

% 3. REGLAS DE ALTA PRIORIDAD (HALLAZGOS ESPECÍFICOS)

% Regla de Ladrillo/Tégula: Indica construcción (Villa o Alfar)
interpretar(P, A, 'Muy Alta', 'Asentamiento Romano', 'Confirmado por tegulas (ladrillo): Indica presencia de techumbre o muros.') :-
    hallazgo_registrado(P, A, Tipo),
    (Tipo = 'tegula_ladrillo'; Tipo = 'Estructura/Muro'), !.

% Regla de Moneda: Indica actividad económica o paso
interpretar(P, A, 'Alta', 'Zona de Actividad Romana', 'Confirmado por moneda: Posible zona de transito o pequeña ocupacion.') :-
    hallazgo_registrado(P, A, 'Moneda'), !.

% 4. DETECCION DE ESTRUCTURAS (Anomalías Geométricas)
% Los romanos nivelaban el terreno. Un "escalon" en zona llana es sospechoso.
interpretar(P, A, 'Alta', 'Cimentacion Enterrada', 'Anomalia detectada: El relieve artificial sugiere una estructura soterrada en terreno arcilloso.') :-
    P > 12, P < 35, % Pendiente fuera de lo común para el entorno
    A > 20,
    preferencia('Romana', 'arcilloso'), !.

% 5. REGLAS DE ANALOGÍA (APRENDIZAJE)
% Si encontraste monedas en una pendiente similar, esta zona es sospechosa.
interpretar(P, _, 'Alta', 'Sugerida por Analogia', 'Patron de relieve identico a tus hallazgos anteriores de monedas.') :-
    hallazgo_registrado(P_ant, _, 'Moneda'),
    abs(P - P_ant) < 0.3, !.

% 6. PATRONES DE INGENIERÍA ROMANA (GENERAL)
interpretar(P, A, Prob, Epoca, Explicacion) :-
    (
        % Villa Romana: Pendiente casi nula (< 3%) y suelo arcilloso (fertil)
        (P < 3, A < 90, preferencia('Romana', 'arcilloso')) -> 
        (Prob = 'Alta', Epoca = 'Romana', Explicacion = 'Llanura arcillosa fertil: Ubicacion tipica de villae agricolas.');
        
        % Camino/Calzada: Pendiente suave y constante
        (P >= 3, P < 6, A < 150) -> 
        (Prob = 'Media', Epoca = 'Romana/Comercial', Explicacion = 'Pendiente constante: Perfil compatible con trazados de calzadas secundarias.');
        
        % Patron Prehistorico
        (P >= 6, P < 12, A > 40) -> 
        (Prob = 'Media-Alta', Epoca = 'Prehistoria', Explicacion = 'Ubicacion en loma: Estrategia de control visual del valle.');
        
        % Por defecto
        (Prob = 'Baja', Epoca = 'Ninguna', Explicacion = 'Relieve natural compatible con erosion estandar.')
    ).

% Predicados de seguridad
hallazgo_registrado(-1, -1, 'ninguno').
hecho_confirmado(-1, -1, 'no').