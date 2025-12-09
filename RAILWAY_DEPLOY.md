# Guía de Deployment en Railway

Esta guía te ayudará a desplegar el backend de AI Music Detector en Railway.

## 📋 Prerrequisitos

1. Una cuenta en [Railway](https://railway.app/)
2. Git instalado en tu computadora
3. El código del backend en un repositorio Git (GitHub, GitLab, etc.)

## 🚀 Pasos para Deployment

### 1. Preparar el Código

El backend ya está preparado con los archivos necesarios:
- ✅ `Procfile` - Define cómo Railway debe ejecutar la app
- ✅ `runtime.txt` - Especifica la versión de Python
- ✅ `requirements.txt` - Lista de dependencias (incluye gunicorn)
- ✅ `railway.json` - Configuración específica de Railway
- ✅ `.env.example` - Plantilla de variables de entorno

### 2. Subir el Código a Git (si aún no lo has hecho)

```bash
cd ai-music-detector-backend

# Inicializar repositorio (si no existe)
git init

# Agregar archivos
git add .

# Commit
git commit -m "Preparar backend para Railway deployment"

# Agregar repositorio remoto (GitHub, GitLab, etc.)
git remote add origin https://github.com/tu-usuario/tu-repo.git

# Push
git push -u origin main
```

### 3. Crear Proyecto en Railway

#### Opción A: Desde GitHub (Recomendado)

1. Ve a [Railway](https://railway.app/)
2. Haz clic en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway para acceder a tu GitHub
5. Selecciona tu repositorio
6. Railway detectará automáticamente que es una app Python y comenzará el deployment

#### Opción B: Desde CLI de Railway

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Deploy
railway up
```

### 4. Configurar Variables de Entorno

En el dashboard de Railway:

1. Ve a tu proyecto
2. Haz clic en la pestaña **"Variables"**
3. Agrega las siguientes variables:

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

**IMPORTANTE**: No necesitas configurar `PORT` - Railway lo asigna automáticamente.

### 5. Configurar CORS (Importante)

Para que tu app React Native pueda conectarse:

- **Desarrollo**: Deja `CORS_ORIGINS=*`
- **Producción**: Cambia a tu dominio específico: `CORS_ORIGINS=https://tu-app.com`

### 6. Verificar el Deployment

Una vez desplegado, Railway te dará una URL pública como:
```
https://tu-app-railway.up.railway.app
```

Prueba los endpoints:

```bash
# Health check
curl https://tu-app-railway.up.railway.app/health

# Info del detector
curl https://tu-app-railway.up.railway.app/api/info
```

### 7. Actualizar el Frontend

En tu archivo `.env` del frontend React Native, actualiza la URL:

```env
EXPO_PUBLIC_API_URL=https://tu-app-railway.up.railway.app
```

## 🔄 Actualizaciones Futuras

Railway se sincroniza automáticamente con tu repositorio Git:

```bash
# Hacer cambios en el código
git add .
git commit -m "Actualización del backend"
git push

# Railway detectará los cambios y hará redeploy automáticamente
```

## 📊 Monitoreo

En el dashboard de Railway puedes:
- Ver logs en tiempo real
- Monitorear uso de recursos
- Configurar alertas
- Ver métricas de rendimiento

## ⚠️ Consideraciones Importantes

### Límites del Plan Gratuito de Railway

- **500 horas de ejecución/mes**
- **100 GB de ancho de banda**
- **8 GB de RAM**
- **8 vCPU**

Para análisis de audio, esto debería ser suficiente para desarrollo y uso moderado.

### Optimizaciones Recomendadas

1. **Workers**: En `Procfile`, ajusta `--workers` según tus necesidades:
   ```
   --workers 2  # Para plan gratuito
   --workers 4  # Para más tráfico
   ```

2. **Timeout**: Ajusta según el tamaño de tus archivos:
   ```
   --timeout 120  # 2 minutos (actual)
   --timeout 300  # 5 minutos para archivos grandes
   ```

3. **Limpieza de archivos**: El sistema limpia archivos temporales automáticamente después del análisis.

### Debugging

Si algo falla, revisa los logs en Railway:

1. Ve a tu proyecto en Railway
2. Haz clic en la pestaña **"Deployments"**
3. Selecciona el deployment más reciente
4. Haz clic en **"View Logs"**

Errores comunes:
- **"Module not found"**: Verifica que todas las dependencias estén en `requirements.txt`
- **"Port already in use"**: Railway maneja esto automáticamente, asegúrate de usar `$PORT` en tu código
- **"Out of memory"**: Reduce el número de workers o actualiza tu plan

## 🆘 Solución de Problemas

### Error: "Application failed to respond"

**Causa**: La app no está escuchando en el puerto correcto.

**Solución**: Verifica que `app.py` use la variable de entorno `PORT`:
```python
PORT = int(os.getenv('PORT', 5000))
app.run(host='0.0.0.0', port=PORT)
```

### Error: "Build failed"

**Causa**: Dependencias incompatibles o faltantes.

**Solución**:
1. Verifica que `requirements.txt` esté completo
2. Asegúrate de que las versiones sean compatibles
3. Revisa los logs de build en Railway

### Error: "502 Bad Gateway"

**Causa**: La aplicación crasheó o no está respondiendo.

**Solución**:
1. Revisa los logs en Railway
2. Verifica que gunicorn esté instalado
3. Comprueba que el `Procfile` sea correcto

## 📚 Recursos Adicionales

- [Documentación de Railway](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## ✅ Checklist Final

Antes de considerar el deployment completo:

- [ ] Backend desplegado en Railway
- [ ] Health check responde correctamente
- [ ] Variables de entorno configuradas
- [ ] CORS configurado correctamente
- [ ] Frontend actualizado con la nueva URL
- [ ] Prueba de análisis de audio exitosa
- [ ] Logs monitoreados sin errores

## 🎉 ¡Listo!

Tu backend ahora está en producción y accesible desde cualquier lugar. Tu app React Native puede conectarse y analizar música generada por IA.
