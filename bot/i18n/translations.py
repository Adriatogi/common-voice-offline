"""Translation strings for all supported bot interface languages."""

TRANSLATIONS = {
    # ==========================================================================
    # ENGLISH
    # ==========================================================================
    "en": {
        # Language selection
        "language_prompt": "🌐 Choose your language / Elige tu idioma:",
        "language_changed": "✅ Language changed to English!",
        "language_current": "Current language: **English**\n\nUse /language to change.",
        
        # Welcome / Help
        "welcome": """
🎙️ **Welcome to the Common Voice Offline Bot!**

This bot helps you contribute voice recordings to Mozilla Common Voice, even in areas with limited connectivity.

**How it works:**
1. /login - Register with your email and username
2. /setup - Select your language and download sentences
3. Go offline and record your voice messages
4. When back online, your recordings upload automatically

**Commands:**
/login - Register for Common Voice
/setup - Select language and download sentences
/sentences - View your assigned sentences
/status - Check your recording progress
/upload - Upload pending recordings
/language - Change bot language
/logout - Clear your session
/help - Show this help

🌐 **Change language:** /language

Ready to start? Use /login to begin!
""",
        
        # Login flow
        "already_logged_in": "You're already logged in as **{username}**!\n\nUse /logout to log out first, or /setup to continue.",
        "login_start": "Let's get you set up with Common Voice!\n\nPlease enter your **email address**:\n\n(This will be used to identify your contributions)\n\nType /cancel to abort.",
        "login_invalid_email": "That doesn't look like a valid email. Please try again:",
        "login_enter_username": "Great! Now please enter a **username** for Common Voice:\n\n(This will be visible in the dataset)",
        "login_invalid_username": "Username must be at least 2 characters. Please try again:",
        "login_creating": "Creating your Common Voice profile...",
        "login_failed": "❌ Failed to create user: {error}\n\nUse /login to try again.",
        "login_success": "✅ **Registration successful!**\n\nWelcome, {username}!\nYour Common Voice User ID: `{cv_user_id}`\n\nNext step: Use /setup to select your language and download sentences.",
        "login_cancelled": "Login cancelled. Use /login to try again.",
        
        # Setup flow
        "setup_not_registered": "You need to register first! Use /login to get started.",
        "setup_select_language": "Let's set up your recording session!\n\nPlease select your **language**:",
        "setup_invalid_language": "Please select a valid language from the options:",
        "setup_select_count": "Great! You selected **{language}**.\n\nHow many sentences would you like to download? (max {max})",
        "setup_invalid_count": "Please enter a number between 1 and {max}:",
        "setup_fetching": "Fetching {count} sentences in {language}...",
        "setup_no_sentences": "❌ No sentences available for {language}.\n\nThis language may not be fully supported yet. Try another language with /setup.",
        "setup_fetch_failed": "❌ Failed to fetch sentences: {error}\n\nUse /setup to try again.",
        "setup_complete": "✅ **Downloaded {count} sentences!**\n\nI'll send them below. When you're offline, record voice messages in this format:\n`#1` followed by your voice recording\n\nThe sentences will stay in your chat history so you can see them offline.",
        "setup_all_sent": "📝 **All sentences sent!**\n\nTo record:\n1. Type `#1` (or any sentence number)\n2. Send a voice message reading that sentence\n\nYour recordings will be uploaded automatically when you're online.\nUse /status to check your progress.",
        "setup_cancelled": "Setup cancelled. Use /setup to try again.",
        
        # Unknown message
        "unknown_message": "I don't understand that message. 🤔\n\nUse /help to see available commands.",
        
        # Recording
        "record_not_registered": "Please register first with /login before recording.",
        "record_no_session": "Please set up your session first with /setup.",
        "record_specify_sentence": "Please specify which sentence you're recording!\n\nSend a message like `#5` first, then your voice recording.",
        "record_not_found": "Sentence #{number} not found. You have sentences #1-#{total}.",
        "record_no_sentences": "You don't have any sentences. Use /setup to download some.",
        "record_prompt": "**#{number}**\n{text}\n\n🎤 Send a voice message now to record this sentence.",
        "record_success": "✅ Recorded #{number}!\n📊 Progress: {recorded}/{total} sentences recorded\n📤 {pending} pending upload • ✓ {uploaded} uploaded",
        "record_uploaded": "☁️ #{number} uploaded to Common Voice!",
        
        # Status
        "status_not_registered": "You're not registered. Use /login to get started.",
        "status_header": "📊 **Your Status**\n",
        "status_user": "👤 User: {username}",
        "status_email": "📧 Email: {email}",
        "status_language": "🌍 Language: {language}",
        "status_sentences": "📝 Sentences: {count}",
        "status_progress_header": "**Recording Progress:**",
        "status_progress_total": "• Total recorded: {recorded}/{total}",
        "status_progress_pending": "• Pending upload: {pending}",
        "status_progress_uploaded": "• Uploaded: {uploaded}",
        "status_progress_failed": "• Failed: {failed}",
        "status_upload_hint": "\n💡 Use /upload to upload pending recordings.",
        "status_no_session": "\n⚠️ No active session. Use /setup to select a language.",
        
        # Sentences list
        "sentences_no_session": "No active session. Use /setup to download sentences.",
        "sentences_none": "No sentences downloaded. Use /setup to download sentences.",
        "sentences_header": "📝 **Your {count} Sentences**\nLegend: ⬜ Not recorded • 🟡 Pending • ✅ Uploaded • ❌ Failed\n",
        
        # Upload
        "upload_not_registered": "You're not registered. Use /login to get started.",
        "upload_no_session": "No active session. Use /setup to get started.",
        "upload_nothing": "No recordings to upload! Record some sentences first.",
        "upload_starting": "📤 Uploading {count} recordings...",
        "upload_success": "✅ Successfully uploaded {count} recordings to Common Voice!",
        "upload_partial": "📤 Upload complete:\n• ✅ Uploaded: {success}\n• ❌ Failed: {failed}\n\nUse /status to see details. Failed recordings can be retried with /upload.",
        
        # Logout
        "logout_not_registered": "You're not registered.",
        "logout_pending_warning": "⚠️ You have {count} recordings pending upload!\n\nUse /upload first to upload them, or send /logout again to confirm.",
        "logout_success": "✅ You have been logged out.\n\nYour local data has been cleared.\nUse /login to register again.",
    },
    
    # ==========================================================================
    # SPANISH
    # ==========================================================================
    "es": {
        # Language selection
        "language_prompt": "🌐 Choose your language / Elige tu idioma:",
        "language_changed": "✅ ¡Idioma cambiado a Español!",
        "language_current": "Idioma actual: **Español**\n\nUsa /language para cambiar.",
        
        # Welcome / Help
        "welcome": """
🎙️ **¡Bienvenido al Bot Offline de Common Voice!**

Este bot te ayuda a contribuir grabaciones de voz a Mozilla Common Voice, incluso en áreas con conectividad limitada.

**Cómo funciona:**
1. /login - Regístrate con tu email y nombre de usuario
2. /setup - Selecciona tu idioma y descarga oraciones
3. Ve offline y graba tus mensajes de voz
4. Cuando vuelvas online, tus grabaciones se suben automáticamente

**Comandos:**
/login - Registrarse en Common Voice
/setup - Seleccionar idioma y descargar oraciones
/sentences - Ver tus oraciones asignadas
/status - Ver tu progreso de grabación
/upload - Subir grabaciones pendientes
/language - Cambiar idioma del bot
/logout - Cerrar sesión
/help - Mostrar esta ayuda

🌐 **Cambiar idioma:** /language

¿Listo para empezar? ¡Usa /login para comenzar!
""",
        
        # Login flow
        "already_logged_in": "Ya has iniciado sesión como **{username}**.\n\nUsa /logout para cerrar sesión, o /setup para continuar.",
        "login_start": "¡Vamos a configurar tu cuenta de Common Voice!\n\nPor favor, ingresa tu **correo electrónico**:\n\n(Se usará para identificar tus contribuciones)\n\nEscribe /cancel para cancelar.",
        "login_invalid_email": "Eso no parece un email válido. Por favor, intenta de nuevo:",
        "login_enter_username": "¡Genial! Ahora ingresa un **nombre de usuario** para Common Voice:\n\n(Será visible en el dataset)",
        "login_invalid_username": "El nombre de usuario debe tener al menos 2 caracteres. Intenta de nuevo:",
        "login_creating": "Creando tu perfil de Common Voice...",
        "login_failed": "❌ Error al crear usuario: {error}\n\nUsa /login para intentar de nuevo.",
        "login_success": "✅ **¡Registro exitoso!**\n\n¡Bienvenido/a, {username}!\nTu ID de usuario de Common Voice: `{cv_user_id}`\n\nSiguiente paso: Usa /setup para seleccionar tu idioma y descargar oraciones.",
        "login_cancelled": "Login cancelado. Usa /login para intentar de nuevo.",
        
        # Setup flow
        "setup_not_registered": "¡Necesitas registrarte primero! Usa /login para comenzar.",
        "setup_select_language": "¡Vamos a configurar tu sesión de grabación!\n\nPor favor, selecciona tu **idioma**:",
        "setup_invalid_language": "Por favor, selecciona un idioma válido de las opciones:",
        "setup_select_count": "¡Genial! Seleccionaste **{language}**.\n\n¿Cuántas oraciones quieres descargar? (máx {max})",
        "setup_invalid_count": "Por favor, ingresa un número entre 1 y {max}:",
        "setup_fetching": "Obteniendo {count} oraciones en {language}...",
        "setup_no_sentences": "❌ No hay oraciones disponibles para {language}.\n\nEste idioma puede no estar totalmente soportado aún. Intenta otro idioma con /setup.",
        "setup_fetch_failed": "❌ Error al obtener oraciones: {error}\n\nUsa /setup para intentar de nuevo.",
        "setup_complete": "✅ **¡{count} oraciones descargadas!**\n\nLas enviaré abajo. Cuando estés offline, graba mensajes de voz en este formato:\n`#1` seguido de tu grabación de voz\n\nLas oraciones quedarán en tu historial de chat para verlas offline.",
        "setup_all_sent": "📝 **¡Todas las oraciones enviadas!**\n\nPara grabar:\n1. Escribe `#1` (o cualquier número de oración)\n2. Envía un mensaje de voz leyendo esa oración\n\nTus grabaciones se subirán automáticamente cuando estés online.\nUsa /status para ver tu progreso.",
        "setup_cancelled": "Configuración cancelada. Usa /setup para intentar de nuevo.",
        
        # Unknown message
        "unknown_message": "No entiendo ese mensaje. 🤔\n\nUsa /help para ver los comandos disponibles.",
        
        # Recording
        "record_not_registered": "Por favor, regístrate primero con /login antes de grabar.",
        "record_no_session": "Por favor, configura tu sesión primero con /setup.",
        "record_specify_sentence": "¡Por favor, especifica qué oración estás grabando!\n\nEnvía un mensaje como `#5` primero, luego tu grabación de voz.",
        "record_not_found": "Oración #{number} no encontrada. Tienes oraciones #1-#{total}.",
        "record_no_sentences": "No tienes oraciones. Usa /setup para descargar algunas.",
        "record_prompt": "**#{number}**\n{text}\n\n🎤 Envía un mensaje de voz ahora para grabar esta oración.",
        "record_success": "✅ ¡Grabado #{number}!\n📊 Progreso: {recorded}/{total} oraciones grabadas\n📤 {pending} pendientes • ✓ {uploaded} subidas",
        "record_uploaded": "☁️ ¡#{number} subido a Common Voice!",
        
        # Status
        "status_not_registered": "No estás registrado. Usa /login para comenzar.",
        "status_header": "📊 **Tu Estado**\n",
        "status_user": "👤 Usuario: {username}",
        "status_email": "📧 Email: {email}",
        "status_language": "🌍 Idioma: {language}",
        "status_sentences": "📝 Oraciones: {count}",
        "status_progress_header": "**Progreso de Grabación:**",
        "status_progress_total": "• Total grabadas: {recorded}/{total}",
        "status_progress_pending": "• Pendientes de subir: {pending}",
        "status_progress_uploaded": "• Subidas: {uploaded}",
        "status_progress_failed": "• Fallidas: {failed}",
        "status_upload_hint": "\n💡 Usa /upload para subir grabaciones pendientes.",
        "status_no_session": "\n⚠️ Sin sesión activa. Usa /setup para seleccionar un idioma.",
        
        # Sentences list
        "sentences_no_session": "Sin sesión activa. Usa /setup para descargar oraciones.",
        "sentences_none": "No hay oraciones descargadas. Usa /setup para descargar oraciones.",
        "sentences_header": "📝 **Tus {count} Oraciones**\nLeyenda: ⬜ Sin grabar • 🟡 Pendiente • ✅ Subida • ❌ Fallida\n",
        
        # Upload
        "upload_not_registered": "No estás registrado. Usa /login para comenzar.",
        "upload_no_session": "Sin sesión activa. Usa /setup para comenzar.",
        "upload_nothing": "¡No hay grabaciones para subir! Graba algunas oraciones primero.",
        "upload_starting": "📤 Subiendo {count} grabaciones...",
        "upload_success": "✅ ¡{count} grabaciones subidas exitosamente a Common Voice!",
        "upload_partial": "📤 Subida completada:\n• ✅ Subidas: {success}\n• ❌ Fallidas: {failed}\n\nUsa /status para ver detalles. Las grabaciones fallidas se pueden reintentar con /upload.",
        
        # Logout
        "logout_not_registered": "No estás registrado.",
        "logout_pending_warning": "⚠️ ¡Tienes {count} grabaciones pendientes de subir!\n\nUsa /upload primero para subirlas, o envía /logout de nuevo para confirmar.",
        "logout_success": "✅ Has cerrado sesión.\n\nTus datos locales han sido eliminados.\nUsa /login para registrarte de nuevo.",
    },
}
