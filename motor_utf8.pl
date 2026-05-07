:- dynamic hecho_confirmado/3.
:- dynamic hallazgo_registrado/3.
:- dynamic estructura_detectada/3.

% --- MOTOR DE INFERENCIA ARQUEOLOGICA (HUELVA) - VERSION 3.0 (HIDRO) ---

% 1. YACIMIENTOS DE REFERENCIA
yacimiento('Dolmen de Soto', 37.35, -6.82, 'arcilloso', 'Prehistoria').
yacimiento('Cista de Niebla', 37.36, -6.68, 'calizo', 'Bronce').
yacimiento('Villa de San Walabonso', 37.39, -6.85, 'ferruginoso', 'Romana').

% 2. GEOLOGIA Y PREFERENCIAS
terreno(37.30, 37.45, -6.90, -6.70, 'arcilloso').
preferencia('Romana', 'arcilloso').
preferencia('Prehistoria', 'calizo').

% 3. REGLAS DE ALTA PRIORIDAD (BASADAS EN EVIDENCIA REAL)
interpretar(P, A, _, 'Muy Alta', 'Asentamiento Romano', 'EVIDENCIA DIRECTA: Tegulas o Muros confirmados en este sector.') :-
    hallazgo_registrado(P, A, Tipo),
    (Tipo = 'tegula_ladrillo'; Tipo = 'Estructura/Muro'), !.

interpretar(P, A, _, 'Alta', 'Zona de Actividad', 'EVIDENCIA DIRECTA: Moneda o material mueble registrado.') :-
    hallazgo_registrado(P, A, 'Moneda'), !.

% 4. NUEVA REGLA: EXPLOTACION AGROPECUARIA (FUSION DE DATOS)
interpretar(P, A, D, 'Muy Alta', 'Villae con Recurso Hidrico', 'ANALISIS GEO-ESPACIAL: Terreno ideal para cultivo y acceso inmediato a agua (menor a 350m).') :-
    P < 4.0,            % Terreno llano para agricultura
    D < 350,            % Muy cerca del rio (distancia en metros)
    A > 15, A < 90,     % Altitud moderada
    preferencia('Romana', 'arcilloso'), !.

% 5. DETECCION DE ESTRUCTURAS (FILTRO RESTRICTIVO)
interpretar(P, A, _, 'Alta', 'Cimentacion Enterrada', 'ANOMALIA TECNICA: Pendiente artificial compatible con cimientos enterrados.') :-
    P > 14, P < 32, 
    A > 25, A < 110, 
    preferencia('Romana', 'arcilloso'), !.

% 6. REGLAS DE ANALOGIA (APRENDIZAJE)
interpretar(P, _, _, 'Media-Alta', 'Sugerida por Analogia', 'SIMILITUD GEOMETRICA: Perfil de relieve casi identico a hallazgo previo.') :-
    hallazgo_registrado(P_ant, _, 'Moneda'),
    abs(P - P_ant) < 0.2, !.

% 7. PATRONES DE INGENIERIA (BARRIDO GENERAL)
interpretar(P, A, D, Prob, Epoca, Explicacion) :-
    (
        % Villa Romana Estandar (Lejos del agua pero buen suelo)
        (P < 2.5, A > 15, A < 85, preferencia('Romana', 'arcilloso')) -> 
        (Prob = 'Alta', Epoca = 'Romana', Explicacion = 'Llanura arcillosa fertil: Ubicacion clasica de villae.');
        
        % Camino/Calzada (Cerca del rio puede ser un puente o vado)
        (P >= 3.5, P < 5.5, D < 100) -> 
        (Prob = 'Alta', Epoca = 'Romana/Infraestructura', Explicacion = 'Pendiente constante cerca de agua: Posible punto de cruce o vado.');
        
        % Patron Prehistorico (Control visual)
        (P >= 8, P < 11, A > 50) -> 
        (Prob = 'Media-Alta', Epoca = 'Prehistoria', Explicacion = 'Posicion estrategica en loma: Control visual del territorio.');
        
        % Por defecto
        (Prob = 'Muy Baja', Epoca = 'Ninguna', Explicacion = 'Relieve compatible con formacion natural.')
    ).

% Predicados de seguridad
hallazgo_registrado(-1, -1, 'ninguno').
hecho_confirmado(-1, -1, 'no').