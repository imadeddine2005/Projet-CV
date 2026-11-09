# Gesture-Controlled Presentation System

> **Projet de Vision par Ordinateur (Computer Vision)**  
> Une application interactive permettant de controller des presentations (PowerPoint et PDF) en temps reel grace aux mouvements de la main via une webcam, combinant **OpenCV**, **MediaPipe** et **PyQt5**.

---

## Sommaire
1. [Apercu du Projet](#apercu-du-projet)
2. [Fonctionnalites Principales](#fonctionnalites-principales)
3. [Guide des Gestes de Controle](#guide-des-gestes-de-controle)
4. [Architecture Technique et Pipeline](#architecture-technique-et-pipeline)
5. [Lien avec les Notions de Vision par Ordinateur (TPs)](#lien-avec-les-notions-de-vision-par-ordinateur-tps)
6. [Structure des Fichiers](#structure-des-fichiers)
7. [Installation et Prerequis](#installation-et-prerequis)
8. [Mode d'Emploi](#mode-demploi)

---

## Apercu du Projet

Ce projet transforme une webcam standard en telecommande intelligente pour vos presentations. Il elimine le besoin d'une souris physique ou d'un pointeur laser traditionnel en detectant les reperes articulaires de la main (21 points cles) en temps reel.

```
Fichier (.ppt / .pptx) 
   |
   +---> Conversion Headless (LibreOffice) ---> Fichier PDF
   |
   +---> Rasterisation (PyMuPDF) ---> Images de Diapositives (PNG)
                                            |
                                            v
Webcam ---> MediaPipe (Landmarks 21 pts) ---> OpenCV (Superposition et Gestes) ---> Interface PyQt5
```

---

## Fonctionnalites Principales

* **Prise en charge des fichiers :** Chargement direct des presentations PowerPoint (.ppt, .pptx).
* **Navigation fluide :** Passage aux diapositives suivantes et precedentes par gestes.
* **Annotation en direct :** Possibilite de dessiner ou souligner des elements directement sur la slide avec l'index.
* **Pointeur Virtuel :** Affichage d'un curseur flottant pour designer une zone precise sans tracer de trait.
* **Gomme et Effacement :** Suppression du dernier trait trace ou effacement complet des annotations.
* **Zone de Declenchement et Anti-rebond :** Detection limitee a une zone dediee (rectangle en pointilles) avec temporisation pour eviter les declenchements involontaires.
* **Personnalisation :** Choix des couleurs d'annotation (Rouge, Bleu, Vert, Jaune) et reglage de la sensibilite de detection.

---

## Guide des Gestes de Controle

L'etat de la main est represente par un vecteur binaire de 5 doigts :  
`[Pouce, Index, Majeur, Annulaire, Auriculaire]`  
(1 = doigt leve, 0 = doigt baisse).

| Action | Doigts Leves | Vecteur binaire | Zone d'execution |
| :--- | :--- | :---: | :--- |
| **Slide Suivante** | Auriculaire seul (petit doigt) | [0, 0, 0, 0, 1] | Rectangle vert (maintenir 1s) |
| **Slide Precedente** | Pouce seul | [1, 0, 0, 0, 0] | Rectangle vert (maintenir 1s) |
| **Dessiner (Draw)** | Index seul | [0, 1, 0, 0, 0] | Partout sur l'ecran |
| **Pointeur Virtuel** | Index et Majeur | [0, 1, 1, 0, 0] | Partout sur l'ecran |
| **Effacer le dernier trait** | Index, Majeur et Annulaire | [0, 1, 1, 1, 0] | Partout sur l'ecran |
| **Effacer tout (Clear All)** | Main ouverte (5 doigts) | [1, 1, 1, 1, 1] | Rectangle vert |
| **Afficher / Masquer l'aide** | Pouce et Index | [1, 1, 0, 0, 0] | Rectangle vert |

---

## Lien avec les Notions de Vision par Ordinateur (TPs)

Ce projet met en pratique plusieurs concepts fondamentaux etudies en travaux pratiques :

1. **Acquisition et Traitement du flux video (TP 1 et TP 3) :**
   * Gestion de la camera via `cv2.VideoCapture`.
   * Inversion horizontale (`cv2.flip`) pour creer un effet miroir ergonomique.
   * Superposition d'elements graphiques (`cv2.putText`, `cv2.circle`, `cv2.line`).

2. **Espaces colorimetriques (TP 2) :**
   * Conversion BGR (standard OpenCV) vers RGB pour alimenter le modele MediaPipe.

3. **Transformations Geometriques et Interpolation (TP 4) :**
   * Interpolation lineaire (`np.interp`) pour mapper les coordonnees de la camera (ex: 640x480) vers la resolution complete de la fenetre de presentation.

4. **Analyse Spatiale et Squelette 2D :**
   * Suivi des 21 reperes anatomiques en temps reel.
   * Calculs de distances euclidiennes et d'angles trigonometriques pour classifier l'etat de chaque doigt (etendu ou replie).

---

## Structure des Fichiers

```text
Projet_CV/
|
+-- main.py              # Application principale (GUI PyQt5, gestion des threads, logique de controle)
+-- HandTracker.py       # Module de detection de main et classification des doigts (MediaPipe)
+-- dottedline.py        # Fonctions utilitaires pour le trace de contours et lignes pointillees
+-- models/
|   +-- hand_landmarker.task # Modele MediaPipe HandLandmarker
+-- requirements.txt     # Dependances Python
+-- README.md            # Documentation du projet
```

---

## Installation et Prerequis

### 1. Se positionner dans le dossier
```bash
cd Projet_CV
```

### 2. Creer et activer l'environnement virtuel (venv)
Sous Windows (PowerShell) :
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Installer les dependances Python
```bash
pip install -r requirements.txt
```

### 4. Dependance Systeme (LibreOffice)
Pour convertir automatiquement les presentations PowerPoint (.pptx) en images de diapositives, LibreOffice doit etre installe sur la machine (necessaire pour la conversion headless).

---

## Mode d'Emploi

1. **Lancer l'application :**
   ```bash
   python main.py
   ```
2. Dans la fenetre de configuration :
   * Cliquer sur **Select PPT File** pour choisir la presentation.
   * Ajuster la sensibilite de detection et la couleur des annotations si souhaite.
   * Cliquer sur **Start Presentation**.
3. Se placer devant la webcam et utiliser les gestes decrits dans le tableau pour naviguer et annoter la presentation.

---

*Projet realise dans le cadre du module de Vision par Ordinateur.*