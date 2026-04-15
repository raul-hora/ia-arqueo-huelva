:- dynamic hecho_confirmado/3.
:- dynamic hallazgo_registrado/3.
:- dynamic estructura_detectada/3.

% --- MOTOR DE INFERENCIA ARQUEOLOGICA (HUELVA) ---

% 1. YACIMIENTOS DE REFERENCIA
yacimiento('Dolmen de Soto', 37.35, -6.82, 'arcilloso', 'Prehistoria').
yacimiento('Cista de Niebla', 37.36, -6.68, 'calizo', 'Bronce').
yacimiento('Villa de San Walabonso', 37.39, -6.85, 'ferruginoso', 'Romana').

% 2. GEOLOGIA
terreno(37.30, 37.45, -6.90, -6.70, 'arcilloso').
preferencia('Romana', 'arcilloso').
preferencia('Prehistoria', 'calizo').

% 3. REGLAS DE ALTA PRIORIDAD (HALLAZGOS Y ESTRUCTURAS)

% Regla 1: Prioridad por hallazgo manual del usuario
interpretar(P, A, 'Muy Alta', Epoca, Explicacion) :-
    hallazgo_registrado(P, A, Tipo),
    Epoca = 'Confirmada por Hallazgo',
    atom_concat('Restos encontrados: ', Tipo, Explicacion), !.

% Regla 2: DETECCION DE ESTRUCTURAS (Irregularidades en el LiDAR)
% Si la pendiente cambia bruscamente en una zona llana (P < 5), es una anomalía
interpretar(P, A, 'Alta', 'Estructura Potencial', 'Anomalia detectada: El relieve indica una posible cimentacion o muro enterrado.') :-
    P > 15, A > 10, % Un "salto" de relieve (pendiente alta local)
    P < 45,         % Pero no es un barranco natural (pendiente extrema)
    terreno(_, _, _, _, 'arcilloso'), !.

% 4. REGLAS DE ANALOGIA
interpretar(P, _, 'Alta', 'Sugerida por Analogia', 'Zona similar a tus hallazgos anteriores.') :-
    hallazgo_registrado(P_ant, _, _),
    abs(P - P_ant) < 0.5, !.

% 5. REGLAS GENERALES (PATRONES DE ASENTAMIENTO)
interpretar(P, A, Prob, Epoca, Explicacion) :-
    terreno(37.30, 37.45, -6.90, -6.70, TipoSuelo),
    (
        % Patron Romano (Llanuras fertiles)
        (P < 3, A > 10, A < 80, preferencia('Romana', TipoSuelo)) -> 
        (Prob = 'Alta', Epoca = 'Romana', Explicacion = 'Terreno optimo para villa agricola o calzada.');
        
        % Patron Prehistorico (Lomas y visibilidad)
        (P >= 3, P < 8, A > 40, A < 120) -> 
        (Prob = 'Media-Alta', Epoca = 'Prehistoria', Explicacion = 'Ubicacion en loma con dominio del paisaje.');
        
        % Caso por defecto
        (Prob = 'Baja', Epoca = 'Ninguna', Explicacion = 'Relieve natural sin patrones arqueologicos claros.')
    ).

% Regla de seguridad para evitar errores de existencia
hallazgo_registrado(-1, -1, 'ninguno').
hecho_confirmado(-1, -1, 'no').