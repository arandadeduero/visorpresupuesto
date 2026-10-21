// Configuración de la analítica: el ÚNICO sitio donde se escribe el ID, la clave de consentimiento, la caducidad del
// rechazo y la política de privacidad. Para desactivar la analítica o cambiar de medidor, se toca aquí (ver README).

/** ID de medición de Google Analytics 4 (el mismo medidor compartido con las webs de fiestas y bienestar animal). */
export const GA_ID = "G-BXMC22W46S";

/** Clave de localStorage donde se recuerda la decisión: {v: "granted" | "denied", t: milisegundos}. */
export const CLAVE_CONSENTIMIENTO = "presupuestosAranda:analytics-consent";

/** «Rechazar» se recuerda 4 días y luego se vuelve a preguntar; «Aceptar» no caduca. */
export const TTL_RECHAZO_MS = 4 * 24 * 60 * 60 * 1000;

/** Política de privacidad del Ayuntamiento, enlazada desde el aviso y el pie. */
export const URL_POLITICA_PRIVACIDAD = "https://www.arandadeduero.es/politica-privacidad/";
