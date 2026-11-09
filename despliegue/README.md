# Despliegue en el servidor

Guía para preparar un servidor virtual (Ubuntu 24.04, alojado en la UE).

## 1. Preparar el servidor

```bash
# Como root, nada más crear el servidor
adduser gemelo && usermod -aG sudo gemelo
rsync --archive --chown=gemelo:gemelo ~/.ssh /home/gemelo
# En /etc/ssh/sshd_config: PermitRootLogin no, PasswordAuthentication no
systemctl restart ssh

ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
apt update && apt install -y unattended-upgrades fail2ban
```

## 2. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker gemelo
```

## 3. DNS

Crea un registro `A` del dominio (o subdominio) apuntando a la IPv4 del servidor.

## 4. Desplegar

```bash
git clone https://github.com/<usuario>/gemelo-profesional.git && cd gemelo-profesional
cp .env.example .env && nano .env      # contraseñas largas y claves de API
DOMINIO=midominio.es docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## 5. Copias de seguridad

```bash
docker compose exec -T db pg_dump -U gemelo gemelo | gzip > copia_$(date +%F).sql.gz
```

Se recomienda activar también las copias automáticas del proveedor.
