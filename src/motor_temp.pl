% --- MOTOR DE INFERENCIA ARQUEOLÓGICA (HUELVA) ---

% 1. LÓGICA PARA ÉPOCA ROMANA (Villas y Explotaciones Agrícolas)
% Patrón: Terreno muy llano (P < 3%) y altitud moderada (cerca de valles).
interpretar(P, A, 'Alta', 'Romana (Posible Villa/Agrícola)', 
    'Terreno óptimo para la agricultura y edificación. Coincide con el patrón de asentamiento rural romano en la Bética.') :- 
    P < 3, A > 10, A < 80, !.

% 2. LÓGICA PARA EDAD DEL BRONCE / CALCOLÍTICO (Dólmenes y Necrópolis)
% Patrón: Pendiente suave (3-7%) en zonas de visibilidad o lomas.
interpretar(P, A, 'Media-Alta', 'Prehistoria (Bronce/Calcolítico)', 
    'Ubicación en loma suave. Patrón común en estructuras megalíticas o necrópolis de la zona de Trigueros.') :- 
    P >= 3, P < 8, A > 40, A < 120, !.

% 3. LÓGICA PARA ASENTAMIENTOS DE VIGILANCIA (Atalayas/Turris)
% Patrón: Pendiente elevada pero en puntos altos.
interpretar(P, A, 'Media', 'Indeterminado (Posible Vigilancia)', 
    'Pendiente elevada en zona alta. Podría tratarse de un punto de control o estructura defensiva.') :- 
    P >= 8, A > 100, !.

% 4. CASO POR DEFECTO
interpretar(_, _, 'Baja', 'Ninguna clara', 'No cumple los patrones de asentamiento conocidos para esta zona.').

% Regla para tus aciertos manuales
interpretar(P, A, 'Confirmada', 'Validado por Arqueólogo', 'Punto verificado manualmente en el terreno.') :- 
    hecho_confirmado(P, A, 'Si').