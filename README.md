# Dokumentation: Jenkins Service für Automatisierte Instanz-Erstellung

## Einführung

Diese Dokumentation dient als Einführung und Leitfaden für die Nutzung unseres Jenkins Services, der es ermöglicht, automatisiert neue Jenkins-Instanzen in Docker-Containern auf einer Hetzner Cloud VM aufzusetzen. Der Service übernimmt dabei das Einrichten eines gewünschten DNS-Eintrags, die Generierung eines SSL-Zertifikats und die Installation von Nginx als Reverse Proxy für HTTPS.

**Hinweis**: Diese Dokumentation richtet sich an interne Kollegen und dient der Demonstration der aktuellen Funktionalität des Projekts.

---

## Überblick über den Service

Der Jenkins Service ermöglicht es, basierend auf einem bereitgestellten Konfigurations-Repository:

- **Automatisiertes Aufsetzen** einer neuen Jenkins-Instanz.
- **Anbindung an einen DNS-Eintrag** unter der Domain `*.comquent.academy`.
- **SSL-Verschlüsselung** durch automatische Zertifikatserstellung.
- **Einrichtung eines Reverse Proxys** mittels Nginx für HTTPS-Zugriff.

---

## Voraussetzungen für die Nutzung

Um den Service nutzen zu können, benötigen Sie:

1. **Zugang zu Jenkins**: Sie erhalten von uns einen Zugang zu einer bestehenden Jenkins-Instanz.
2. **Konfigurations-Repository**: Ein GitHub-Repository, das Ihre individuellen Konfigurationsdateien enthält (siehe unten).
3. **Start des passenden Jenkins-Jobs**: Entweder den `jenkins-setup` Job oder den `jenkins-env-automation` Job, je nach Bedarf.

---

## Verfügbare Jenkins-Jobs

### 1. **`BuildImage`**

- **Funktion**: Erstellt das Python-Image, das für die Ausführung der anderen beiden Jobs erforderlich ist.
- **Hinweis**: Dieser Job muss **einmalig ausgeführt werden**, bevor die Jobs `jenkins-setup` und `jenkins-env-automation` genutzt werden können.

### 2. **`jenkins-setup`**

- **Funktion**: Setzt eine neue Jenkins-Instanz mit der gewünschten Konfiguration auf.
- **Parameter**:
  - **Domain**: Muss aktuell auf `.comquent.academy` enden.
  - **Konfigurations-Repository**: URL zu Ihrem GitHub-Repository.
  - **Branch** (optional): Falls Sie einen spezifischen Branch nutzen möchten.

### 3. **`jenkins-env-automation`**

- **Funktion**: Führt das komplette Setup durch, inklusive Aufbau und Abbau der Umgebung. Dient als Test-Pipeline.
- **Parameter**: Gleich wie bei `jenkins-setup`.

### 4. **`docker-test`**

- **Funktion**: Wird automatisch beim Start ausgeführt, um die Docker-Funktionalität zu testen.
- **Hinweis**: Um den `docker-test` Job nutzen zu können, muss Ihr Docker-Image entsprechend konfiguriert sein (siehe weiter unten).
---

## Aufbau des Konfigurations-Repositories

Ihr Repository muss folgende Dateien enthalten:

1. **YAML-Datei(en)**: Definieren die Jenkins-Konfiguration mittels [Jenkins Configuration as Code (JCasC)](https://jenkins.io/projects/jcasc/).
2. **`plugins.txt`**: Liste der gewünschten Jenkins-Plugins, die installiert werden sollen.
3. **`Dockerfile`**: Konfiguration des Jenkins-Docker-Images.

### Anforderungen an die YAML-Konfigurationsdateien

- **Benutzerverwaltung**: Da das Credential Management noch nicht vollständig implementiert ist, muss in der YAML-Konfiguration folgendes festgelegt werden:

  ```yaml
  jenkins:
    securityRealm:
      local:
        allowsSignup: false
        users:
          - id: "${ADMIN_USER}"
            password: "${ADMIN_PASS}"
  ```

  - ${ADMIN_USER} und ${ADMIN_PASS} müssen als id und password in der YAML-Konfiguration festgelegt sein. Dadurch werden die Zugangsdaten von der ursprünglichen Jenkins-Instanz auf die neue Instanz übertragen, sodass Benutzername und Passwort beim Einloggen identisch sind.
  - **Hinweis**: Dies ist ein temporärer Workaround und wird in zukünftigen Versionen durch eine sichere Credential-Verwaltung ersetzt.
---
### Möglichkeit zum Bootstrap der Jenkins-Instanz

Sie können auch eine Kopie der Ausgangsinstanz erstellen, indem Sie das folgende Konfigurations-Repository und den entsprechenden Branch verwenden:

```
Konfigurations-Repository: https://github.com/cqNikolaus/jenkins_configs
Branch: bootstrap
```

Hinweis: Diese Funktion kann nützlich sein, um eine identische Kopie der bestehenden Jenkins-Instanz zu erstellen oder um schnell eine vorkonfigurierte Umgebung zu erhalten.



---

## Anleitung zur Erstellung des Dockerfiles

Ihr `Dockerfile` sollte ähnlich wie das folgende Beispiel aufgebaut sein und muss den Namen 'Dockerfile' tragen:

```dockerfile
FROM jenkins/jenkins:lts

USER root

# Installation von notwendigen Paketen und Docker CLI
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli

# Hinzufügen des Jenkins-Benutzers zur Docker-Gruppe
RUN groupadd -f docker && usermod -aG docker jenkins

# Kopieren der Plugins-Liste und Installation der Plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt

# Kopieren der eigenen YAML-Konfigurationen
COPY *.yaml /var/jenkins_home/casc_configs/

# Klonen des notwendigen Repositories für den `docker-test` Job
RUN mkdir -p /var/jenkins_home/casc_configs && \
    chown -R jenkins:jenkins /var/jenkins_home/casc_configs && \
    git clone https://github.com/cqNikolaus/jenkins_automation /tmp/repo && \
    cp /tmp/repo/*.yaml /var/jenkins_home/casc_configs/ && \
    rm -rf /tmp/repo

# Setzen der Umgebungsvariablen für JCasC und Deaktivierung des Setup-Wizards
ENV CASC_JENKINS_CONFIG /var/jenkins_home/casc_configs
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
```

### Wichtige Punkte:

- **Docker CLI Installation**: Die Installation von `docker-ce-cli` (oder alternativ `docker.io`) ist notwendig, damit der Container auf die Docker-Funktionen des Hosts zugreifen kann, was für den `docker-test` Job erforderlich ist.

- **Hinzufügen zur Docker-Gruppe**: Durch `groupadd` und `usermod` wird der `jenkins` Benutzer zur Docker-Gruppe hinzugefügt, um die notwendigen Berechtigungen zu erhalten.

- **Klonen des Repositories**: Das Klonen des Repositories `jenkins_automation` ist notwendig, um den `docker-test` Job und weitere Pipelines einzubinden.

  ```dockerfile
  RUN mkdir -p /var/jenkins_home/casc_configs && \
      chown -R jenkins:jenkins /var/jenkins_home/casc_configs && \
      git clone https://github.com/cqNikolaus/jenkins_automation /tmp/repo && \
      cp /tmp/repo/*.yaml /var/jenkins_home/casc_configs/ && \
      rm -rf /tmp/repo
  ```

- **Setzen der Umgebungsvariablen**: `CASC_JENKINS_CONFIG` weist Jenkins an, die Konfigurationen aus dem angegebenen Verzeichnis zu laden.

- **Deaktivierung des Setup-Wizards**: Durch Setzen von `JAVA_OPTS` wird der initiale Setup-Wizard von Jenkins übersprungen.

- **Benutzerwechsel**: Am Ende wird zurück zum `jenkins` Benutzer gewechselt.


---

## Zusätzliche Hinweise

- **Berechtigungen**: Es ist wichtig, dass die Berechtigungen für `/var/jenkins_home/casc_configs` korrekt gesetzt sind, damit Jenkins darauf zugreifen kann.

- **Plugins**: Stellen Sie sicher, dass Ihre `plugins.txt` alle benötigten Plugins enthält und korrekt kopiert und installiert wird.

- **Flexibilität**: Obwohl das obige `Dockerfile` ein Beispiel ist, können Sie Anpassungen vornehmen, solange die grundlegenden Anforderungen erfüllt sind.

---

## Aktuelle Einschränkungen und zukünftige Entwicklungen

- **Credential Management**: Derzeit werden die Zugangsdaten unsicher eingebunden. In zukünftigen Versionen wird ein zentrales Credential Management (z.B. mittels HashiCorp Vault) implementiert.

- **Parameterisierung**: Geplant ist eine erweiterte Parameterisierung, um beispielsweise die Anzahl der zu erstellenden Jenkins-Instanzen festlegen zu können.

- **Fehlerbehandlung**: Die Skripte werden in zukünftigen Versionen eine umfangreichere Fehlerbehandlung erhalten.


