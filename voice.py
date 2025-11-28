from gtts import gTTS
import pygame
import tempfile
import os

def speak_text(text):
    try:
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            temp_path = tmp.name

        # Gerar o áudio com gTTS
        tts = gTTS(text=text, lang="pt")
        tts.save(temp_path)

        # Tocar usando pygame
        pygame.mixer.init()
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()

        # Esperar terminar
        while pygame.mixer.music.get_busy():
            pass

    except Exception as e:
        print("Erro ao tentar falar o texto:", e)

    finally:
        # Encerrar mixer e apagar o áudio temporário
        try:
            pygame.mixer.music.unload()
            pygame.mixer.quit()
        except:
            pass

        if os.path.exists(temp_path):
            os.remove(temp_path)
