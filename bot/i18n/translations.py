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
/skip - Skip sentences (or reply "skip")
/resend - Resend unrecorded sentences
/language - Change bot language
/logout - Log out
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
        "login_logging_in": "Logging you in...",
        "login_failed": "❌ Failed to create user: {error}\n\nUse /login to try again.",
        "login_success": "✅ **Registration successful!**\n\nWelcome, {username}!\nUser ID: `{cv_user_id}`\n\n💡 Save this ID to view your stats on the dashboard.\n\nNext step: Use /setup to select your language and download sentences.",
        "login_welcome_back": "✅ **Welcome back, {username}!**\n\nUser ID: `{cv_user_id}`\n\nUse /setup to continue recording, or /status to see your progress.",
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
        "setup_complete": "✅ **Downloaded {count} sentences!**\n\nSending them now as individual messages...",
        "setup_all_sent": "📝 **All sentences sent!**\n\n**To record (works offline!):**\nReply to any sentence above with a voice message.\n\nRecordings upload automatically when online.\nUse /status to check progress.",
        "setup_cancelled": "Setup cancelled. Use /setup to try again.",
        
        # Demographics (age/gender)
        "setup_select_age": "What is your **age range**? (Optional - helps improve voice recognition)",
        "setup_select_gender": "What is your **gender**? (Optional - helps improve voice recognition)",
        "setup_skip": "⏭️ Skip",
        "age_teens": "18-19",
        "age_twenties": "20-29",
        "age_thirties": "30-39",
        "age_forties": "40-49",
        "age_fifties": "50-59",
        "age_sixties": "60-69",
        "age_seventies": "70-79",
        "age_eighties": "80-89",
        "age_nineties": "90+",
        "gender_male": "Male",
        "gender_female": "Female",
        "gender_non_binary": "Non-binary",
        "gender_prefer_not": "Prefer not to say",
        
        # Unknown message / command
        "unknown_message": "I don't understand that message. 🤔\n\nUse /help to see available commands.",
        "unknown_command": "Unknown command. 🤔\n\nUse /help to see available commands.",
        
        # Recording
        "record_not_registered": "Please register first with /login before recording.",
        "record_no_session": "Please set up your session first with /setup.",
        "record_specify_sentence": "Please specify which sentence you're recording!\n\nReply to a sentence message with your voice recording, or send a voice message with `#5` as caption.",
        "record_not_found": "Sentence #{number} not found. You have sentences #1-#{total}.",
        "record_no_sentences": "You don't have any sentences. Use /setup to download some.",
        "record_prompt": "**#{number}**\n{text}",
        "record_success": "✅ Recorded #{number}!\n📊 Progress: {recorded}/{total} sentences recorded\n📤 {pending} pending upload • ✓ {uploaded} uploaded",
        "record_uploaded": "☁️ #{number} uploaded to Common Voice!",
        
        # Status
        "status_not_registered": "You're not registered. Use /login to get started.",
        "status_header": "📊 **Your Status**\n",
        "status_user": "👤 User: {username}",
        "status_user_id": "🆔 User ID: `{user_id}`",
        "status_email": "📧 Email: {email}",
        "status_language": "🌍 Language: {language}",
        "status_sentences": "📝 Sentences: {count}",
        "status_progress_header": "**Progress for {language}:**",
        "status_progress_remaining": "• ⬜ Remaining: {remaining}",
        "status_progress_pending": "• 🟡 Pending upload: {pending}",
        "status_progress_uploaded": "• ✅ Uploaded: {uploaded}",
        "status_progress_skipped": "• ⏭️ Skipped: {skipped}",
        "status_progress_failed": "• ❌ Failed: {failed}",
        "status_upload_hint": "\n💡 /upload to upload pending recordings",
        "status_remaining_hint": "💡 /sentences left to see remaining | /resend to resend",
        "status_no_session": "\n⚠️ No active session. Use /setup to select a language.",
        "status_logged_out": "⚠️ **You are logged out.** Use /login to log in.",
        
        # Sentences list
        "sentences_no_session": "No active session. Use /setup to download sentences.",
        "sentences_none": "No sentences downloaded. Use /setup to download sentences.",
        
        # Resend
        "resend_no_session": "No active session. Use /setup to download sentences first.",
        "resend_no_sentences": "No sentences to resend. Use /setup to download sentences.",
        "resend_all_done": "🎉 All sentences recorded! Use /upload to upload pending, or /setup for more.",
        "resend_starting": "📤 Sending {count} unrecorded sentences...",
        "resend_done": "✅ **Done!** Reply to any sentence above with a voice message to record.",
        "sentences_header": "📝 **Your {count} Sentences**\nLegend: ⬜ Not recorded • 🟡 Pending • ✅ Uploaded • ⏭️ Skipped • ❌ Failed\n\n💡 `/sentences left` - unrecorded only | `/resend` - for offline recording\n",
        "sentences_left_header": "📝 **{count} Sentences Left to Record**\n",
        "sentences_all_done": "🎉 You've recorded all your sentences!\n\nUse /upload to upload pending recordings, or /setup to get more sentences.",
        
        # Upload
        "upload_not_registered": "You're not registered. Use /login to get started.",
        "upload_no_session": "No active session. Use /setup to get started.",
        "upload_nothing": "No recordings to upload! Record some sentences first.",
        "upload_starting": "📤 Uploading {count} recordings...",
        "upload_success": "✅ Successfully uploaded {count} recordings to Common Voice!",
        "upload_partial": "📤 Upload complete:\n• ✅ Uploaded: {success}\n• ❌ Failed: {failed}\n\nUse /status to see details. Failed recordings can be retried with /upload.",
        
        # Skip
        "skip_no_session": "No active session. Use /setup to download sentences first.",
        "skip_no_sentences": "No sentences to skip. Use /setup to download sentences.",
        "skip_word": "skip",  # Word users can reply to skip a sentence
        "skip_usage": "Usage: `/skip 1` or `/skip 1,3,5` or `/skip 1-5`\n\nThis marks sentences as done so they won't be assigned again.\nYou have sentences #1-#{total}.",
        "skip_invalid": "No valid sentence numbers found. You have sentences #1-#{total}.",
        "skip_success": "⏭️ Skipped: {numbers}\n\nThese sentences won't be assigned again.",
        "skip_none_found": "No matching sentences found to skip.",
        
        
        # Logout
        "logout_not_registered": "You're not registered.",
        "logout_already_logged_out": "You're already logged out. Use /login to log in again.",
        "logout_pending_warning": "⚠️ You have {count} recordings pending upload!\n\nUse /upload first to upload them, or send /logout again to confirm.",
        "logout_success": "✅ You have been logged out.\n\nYour contribution history is preserved.\nUse /login to log back in or switch accounts.",
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
/skip - Saltar oraciones (o responde "saltar")
/resend - Reenviar oraciones no grabadas
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
        "login_logging_in": "Iniciando sesión...",
        "login_failed": "❌ Error al crear usuario: {error}\n\nUsa /login para intentar de nuevo.",
        "login_success": "✅ **¡Registro exitoso!**\n\n¡Bienvenido/a, {username}!\nID de usuario: `{cv_user_id}`\n\n💡 Guarda este ID para ver tus estadísticas en el dashboard.\n\nSiguiente paso: Usa /setup para seleccionar tu idioma y descargar oraciones.",
        "login_welcome_back": "✅ **¡Bienvenido/a de vuelta, {username}!**\n\nID de usuario: `{cv_user_id}`\n\nUsa /setup para continuar grabando, o /status para ver tu progreso.",
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
        "setup_complete": "✅ **¡{count} oraciones descargadas!**\n\nEnviándolas ahora como mensajes individuales...",
        "setup_all_sent": "📝 **¡Todas las oraciones enviadas!**\n\n**Para grabar (¡funciona offline!):**\nResponde a cualquier oración arriba con un mensaje de voz.\n\nLas grabaciones se suben automáticamente cuando estés online.\nUsa /status para ver tu progreso.",
        "setup_cancelled": "Configuración cancelada. Usa /setup para intentar de nuevo.",
        
        # Demographics (age/gender)
        "setup_select_age": "¿Cuál es tu **rango de edad**? (Opcional - ayuda a mejorar el reconocimiento de voz)",
        "setup_select_gender": "¿Cuál es tu **género**? (Opcional - ayuda a mejorar el reconocimiento de voz)",
        "setup_skip": "⏭️ Saltar",
        "age_teens": "18-19",
        "age_twenties": "20-29",
        "age_thirties": "30-39",
        "age_forties": "40-49",
        "age_fifties": "50-59",
        "age_sixties": "60-69",
        "age_seventies": "70-79",
        "age_eighties": "80-89",
        "age_nineties": "90+",
        "gender_male": "Masculino",
        "gender_female": "Femenino",
        "gender_non_binary": "No binario",
        "gender_prefer_not": "Prefiero no decir",
        
        # Unknown message / command
        "unknown_message": "No entiendo ese mensaje. 🤔\n\nUsa /help para ver los comandos disponibles.",
        "unknown_command": "Comando desconocido. 🤔\n\nUsa /help para ver los comandos disponibles.",
        
        # Recording
        "record_not_registered": "Por favor, regístrate primero con /login antes de grabar.",
        "record_no_session": "Por favor, configura tu sesión primero con /setup.",
        "record_specify_sentence": "¡Por favor, especifica qué oración estás grabando!\n\nResponde a un mensaje de oración con tu grabación de voz, o envía un mensaje de voz con `#5` como descripción.",
        "record_not_found": "Oración #{number} no encontrada. Tienes oraciones #1-#{total}.",
        "record_no_sentences": "No tienes oraciones. Usa /setup para descargar algunas.",
        "record_prompt": "**#{number}**\n{text}",
        "record_success": "✅ ¡Grabado #{number}!\n📊 Progreso: {recorded}/{total} oraciones grabadas\n📤 {pending} pendientes • ✓ {uploaded} subidas",
        "record_uploaded": "☁️ ¡#{number} subido a Common Voice!",
        
        # Status
        "status_not_registered": "No estás registrado. Usa /login para comenzar.",
        "status_header": "📊 **Tu Estado**\n",
        "status_user": "👤 Usuario: {username}",
        "status_user_id": "🆔 ID de usuario: `{user_id}`",
        "status_email": "📧 Email: {email}",
        "status_language": "🌍 Idioma: {language}",
        "status_sentences": "📝 Oraciones: {count}",
        "status_progress_header": "**Progreso en {language}:**",
        "status_progress_remaining": "• ⬜ Restantes: {remaining}",
        "status_progress_pending": "• 🟡 Pendientes de subir: {pending}",
        "status_progress_uploaded": "• ✅ Subidas: {uploaded}",
        "status_progress_skipped": "• ⏭️ Saltadas: {skipped}",
        "status_progress_failed": "• ❌ Fallidas: {failed}",
        "status_upload_hint": "\n💡 /upload para subir grabaciones pendientes",
        "status_remaining_hint": "💡 /sentences left para ver restantes | /resend para reenviar",
        "status_no_session": "\n⚠️ Sin sesión activa. Usa /setup para seleccionar un idioma.",
        "status_logged_out": "⚠️ **Has cerrado sesión.** Usa /login para iniciar sesión.",
        
        # Sentences list
        "sentences_no_session": "Sin sesión activa. Usa /setup para descargar oraciones.",
        "sentences_none": "No hay oraciones descargadas. Usa /setup para descargar oraciones.",
        
        # Resend
        "resend_no_session": "Sin sesión activa. Usa /setup para descargar oraciones primero.",
        "resend_no_sentences": "No hay oraciones para reenviar. Usa /setup para descargar oraciones.",
        "resend_all_done": "🎉 ¡Todas las oraciones grabadas! Usa /upload para subir pendientes, o /setup para más.",
        "resend_starting": "📤 Enviando {count} oraciones sin grabar...",
        "resend_done": "✅ **¡Listo!** Responde a cualquier oración arriba con un mensaje de voz para grabar.",
        "sentences_header": "📝 **Tus {count} Oraciones**\nLeyenda: ⬜ Sin grabar • 🟡 Pendiente • ✅ Subida • ⏭️ Saltada • ❌ Fallida\n\n💡 `/sentences left` - solo pendientes | `/resend` - para grabar offline\n",
        "sentences_left_header": "📝 **{count} Oraciones Pendientes de Grabar**\n",
        "sentences_all_done": "🎉 ¡Has grabado todas tus oraciones!\n\nUsa /upload para subir las pendientes, o /setup para obtener más oraciones.",
        
        # Upload
        "upload_not_registered": "No estás registrado. Usa /login para comenzar.",
        "upload_no_session": "Sin sesión activa. Usa /setup para comenzar.",
        "upload_nothing": "¡No hay grabaciones para subir! Graba algunas oraciones primero.",
        "upload_starting": "📤 Subiendo {count} grabaciones...",
        "upload_success": "✅ ¡{count} grabaciones subidas exitosamente a Common Voice!",
        "upload_partial": "📤 Subida completada:\n• ✅ Subidas: {success}\n• ❌ Fallidas: {failed}\n\nUsa /status para ver detalles. Las grabaciones fallidas se pueden reintentar con /upload.",
        
        # Skip
        "skip_no_session": "Sin sesión activa. Usa /setup para descargar oraciones primero.",
        "skip_no_sentences": "No hay oraciones para saltar. Usa /setup para descargar oraciones.",
        "skip_word": "saltar",  # Word users can reply to skip a sentence
        "skip_usage": "Uso: `/skip 1` o `/skip 1,3,5` o `/skip 1-5`\n\nEsto marca las oraciones como hechas para que no se asignen de nuevo.\nTienes oraciones #1-#{total}.",
        "skip_invalid": "No se encontraron números de oración válidos. Tienes oraciones #1-#{total}.",
        "skip_success": "⏭️ Saltadas: {numbers}\n\nEstas oraciones no se asignarán de nuevo.",
        "skip_none_found": "No se encontraron oraciones coincidentes para saltar.",
        
        # Logout
        "logout_not_registered": "No estás registrado.",
        "logout_already_logged_out": "Ya has cerrado sesión. Usa /login para iniciar sesión de nuevo.",
        "logout_pending_warning": "⚠️ ¡Tienes {count} grabaciones pendientes de subir!\n\nUsa /upload primero para subirlas, o envía /logout de nuevo para confirmar.",
        "logout_success": "✅ Has cerrado sesión.\n\nTu historial de contribuciones se ha preservado.\nUsa /login para volver a iniciar sesión o cambiar de cuenta.",
    },
}
