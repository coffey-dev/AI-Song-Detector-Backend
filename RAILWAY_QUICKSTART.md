# 🚀 Railway Deploy - Guía Rápida

## Problema Actual

Si intentaste desplegar desde el repositorio principal y obtuviste errores de Expo/React Native, es porque Railway está tratando de ejecutar el frontend en lugar del backend.

## ✅ Solución: Repositorio Separado para Backend

### Paso 1: Crear un nuevo repositorio en GitHub

1. Ve a GitHub y crea un nuevo repositorio:
   - Nombre: `ai-music-detector-backend`
   - Público o Privado (tu elección)
   - NO agregues README, .gitignore, ni license (ya los tienes)

### Paso 2: Subir solo el backend

Abre una terminal en el directorio del backend:

```bash
# Navegar al directorio del backend
cd ai-music-detector-backend

# Inicializar git en este directorio
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Backend inicial para Railway deployment"

# Conectar con tu nuevo repositorio (reemplaza con tu URL)
git remote add origin https://github.com/TU-USUARIO/ai-music-detector-backend.git

# Subir el código
git branch -M main
git push -u origin main
```

### Paso 3: Desplegar en Railway

1. Ve a [Railway](https://railway.app/)
2. Clic en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Elige el repositorio **`ai-music-detector-backend`** (el nuevo)
5. Railway detectará automáticamente que es Python y usará el `Procfile`

### Paso 4: Configurar Variables de Entorno

En Railway dashboard, agrega estas variables:

```env
FLASK_ENV=production
FLASK_DEBUG=0
HOST=0.0.0.0
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=mp3,wav,ogg,m4a,flac,aac
CORS_ORIGINS=*
LOG_LEVEL=INFO
DEV_MODE=False
```

### Paso 5: Obtener la URL

Railway te dará una URL como:
```
https://ai-music-detector-backend-production-xxxx.up.railway.app
```

### Paso 6: Actualizar el Frontend

En tu proyecto React Native, actualiza el archivo `.env`:

```env
EXPO_PUBLIC_API_URL=https://tu-url-de-railway.up.railway.app
```

Reinicia Expo:
```bash
# Ctrl+C para detener
npm start
```

---

## 🎯 Alternativa: Usar un Subdirectorio (Más Complejo)

Si prefieres mantener todo en un solo repositorio:

### 1. Crear `railway.toml` en la raíz del proyecto

Crea este archivo en `C:\Users\Usuario\AI-song-detector\railway.toml`:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "cd ai-music-detector-backend && pip install -r requirements.txt"

[deploy]
startCommand = "cd ai-music-detector-backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
```

### 2. Configurar Railway

En Railway:
1. Ve a Settings
2. En "Build & Deploy", asegúrate de que esté usando el `railway.toml`
3. Redeploy

---

## ✅ Verificación

Una vez desplegado, prueba:

```bash
# Health check
curl https://tu-url.up.railway.app/health

# Info del detector
curl https://tu-url.up.railway.app/api/info
```

Deberías ver respuestas JSON exitosas.

---

## 🆘 Si sigues teniendo problemas

1. **Revisa los logs en Railway**:
   - Dashboard → Tu proyecto → Deployments → View Logs

2. **Verifica que no esté ejecutando Expo**:
   - Los logs NO deben mostrar "expo start"
   - Deben mostrar "Starting gunicorn"

3. **Asegúrate de que el `Procfile` existe**:
   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

---

## 💡 Resumen

**IMPORTANTE**:
- ❌ NO despliegues el frontend de React Native en Railway
- ✅ SÍ despliega solo el backend de Python
- 📱 El frontend se ejecuta en tu teléfono/emulador con Expo
- 🔌 El backend corre en Railway y el frontend se conecta a él vía HTTP

El frontend (React Native) y el backend (Flask) son proyectos separados que se comunican por HTTP. Solo el backend va a Railway.
