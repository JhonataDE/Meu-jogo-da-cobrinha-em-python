import pygame
import random
import sys
import os

pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

# --- Configurações ---
LARGURA, ALTURA_JOGO = 800, 600
PAINEL_TOPO = 40
ALTURA = ALTURA_JOGO + PAINEL_TOPO
TAMANHO_BLOCO = 20
CORES_COMIDA = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
]

BOTAO_LARG = 360
BOTAO_ALT = 72
BOTAO_RADIUS = 14
som_ativo = True
cores_cobra = [(0, 200, 0), (0, 0, 200), (200, 0, 0)]
indice_cor_cobra = 0
borda_ativa = True

# Tela e fundo
pygame.display.set_caption("Jogo Snake")
TELA = pygame.display.set_mode((LARGURA, ALTURA))

# Carregar fundo (se falhar, usa cor sólida)
fundo = None
if os.path.exists("fundo.jpg"):
    try:
        fundo = pygame.image.load("fundo.jpg").convert()
        fundo = pygame.transform.smoothscale(fundo, (LARGURA, ALTURA))
    except Exception:
        fundo = None

# Carregar imagens do troféu e ampulheta
img_trofeu = pygame.image.load("trofeu.png").convert_alpha()
img_ampulheta = pygame.image.load("ampulheta.png").convert_alpha()

# Redimensionar (se precisar)
img_trofeu = pygame.transform.scale(img_trofeu, (40, 30))  
img_ampulheta = pygame.transform.scale(img_ampulheta, (60, 40))  

# Sons (opcionais)
def try_load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None

som_comer = try_load_sound("comer.wav")
som_gameover = try_load_sound("gameover.wav")
hover_sound = try_load_sound("hover.wav")
click_sound = try_load_sound("click.wav")

def tocar_sfx(sound):
    if som_ativo:
        try:
            sound.play()
        except:
            pass

def tocar_musica_menu():
    if not som_ativo:
        return
    try:
        pygame.mixer.music.load("musica_menu.wav")  # se tiver
    except:
        try:
            pygame.mixer.music.load("musica.wav")   # fallback
        except:
            return
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

def tocar_musica_jogo():
    if not som_ativo:
        return
    try:
        pygame.mixer.music.load("musica_jogo.wav")  # se tiver
    except:
        try:
            pygame.mixer.music.load("musica.wav")   # fallback
        except:
            return
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)


# Música de fundo (opcional)
MUSICA = "musica.wav"

# Clock
clock = pygame.time.Clock()

# Cores
VERDE = (0, 128, 0)
PRETO = (0, 0, 0)
AMARELO = (255, 255, 0)
VERMELHO = (255, 0, 0)
BRANCO = (255, 255, 255)
COR_BOTAO = (50, 150, 50)
COR_BOTAO_HOVER = (70, 200, 70)
BORDA_BOTAO = (255, 255, 255)

# Fonte
try:
    FONTE = pygame.font.Font("pixel.ttf", 28)
    FONTE_TITULO = pygame.font.Font("pixel.ttf", 42)
except Exception:
    FONTE = pygame.font.SysFont(None, 28)
    FONTE_TITULO = pygame.font.SysFont(None, 42)

# --- Auxiliares ---

def cor_aleatoria():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))


def forma_aleatoria():
    return random.choice(["quadrado", "circulo", "triangulo", "hexagono"])


def gerar_comida():
    x = random.randrange(0, LARGURA, TAMANHO_BLOCO)
    y = random.randrange(PAINEL_TOPO, ALTURA, TAMANHO_BLOCO)
    return x, y


def carregar_recorde(modo):
    try:
        with open(f"recorde_{modo}.txt", "r") as f:
            return int(f.read())
    except Exception:
        return 0


def salvar_recorde(modo, pontos):
    recorde_atual = carregar_recorde(modo)
    if pontos > recorde_atual:
        with open(f"recorde_{modo}.txt", "w") as f:
            f.write(str(pontos))


# interpolation de cores
def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# Criar superfície bonita de botão (pré-renderizada)
def create_button_surface(size, radius, top_color, bottom_color, text, font, icon_surf=None):
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # sombra
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 6, w - 8, h - 8), border_radius=radius)
    surf.blit(shadow, (0, 0))

    # gradiente vertical (desenhado uma vez por botão)
    for y in range(h):
        t = y / max(1, h - 1)
        color = lerp_color(top_color, bottom_color, t)
        pygame.draw.line(surf, color, (0, y), (w, y))

    # arredondar bordas (rect por cima com blend)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    # borda fina
    pygame.draw.rect(surf, (255, 255, 255, 30), (0, 0, w, h), width=2, border_radius=radius)

    # texto (com sombra)
    text_surf = font.render(text, True, (255, 255, 255))
    text_shadow = font.render(text, True, (0, 0, 0))

    # posição do texto considerando ícone
    icon_offset = 0
    if icon_surf is not None:
        icon_offset = icon_surf.get_width() + 12
        icon_y = (h - icon_surf.get_height()) // 2
        surf.blit(icon_surf, (12, icon_y))

    tx = 16 + icon_offset
    ty = (h - text_surf.get_height()) // 2
    surf.blit(text_shadow, (tx + 2, ty + 2))
    surf.blit(text_surf, (tx, ty))

    return surf


# Classe UIButton
class UIButton:
    def __init__(self, text, rect, font, top_color, bottom_color, icon_path=None, radius=BOTAO_RADIUS):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.radius = radius
        self.text = text
        self.top_color = top_color
        self.bottom_color = bottom_color

        self.icon = None
        if icon_path and os.path.exists(icon_path):
            try:
                img = pygame.image.load(icon_path).convert_alpha()
                ih = self.rect.height - 24
                self.icon = pygame.transform.smoothscale(img, (ih, ih))
            except Exception:
                self.icon = None

        self.base_surf = create_button_surface(self.rect.size, self.radius, top_color, bottom_color, text, font, self.icon)

        brighter_top = tuple(min(255, c + 20) for c in top_color)
        brighter_bot = tuple(min(255, c + 20) for c in bottom_color)
        self.hover_surf = create_button_surface(self.rect.size, self.radius, brighter_top, brighter_bot, text, font, self.icon)

        darker_top = tuple(max(0, c - 40) for c in top_color)
        darker_bot = tuple(max(0, c - 40) for c in bottom_color)
        self.pressed_surf = create_button_surface(self.rect.size, self.radius, darker_top, darker_bot, text, font, self.icon)

        self._hovered = False
        self._pressed = False

    def draw(self, surface):
        if self._pressed:
            surf = self.pressed_surf
            draw_pos = (self.rect.x, self.rect.y + 3)
        elif self._hovered:
            surf = self.hover_surf
            draw_pos = (self.rect.x, self.rect.y - 2)
        else:
            surf = self.base_surf
            draw_pos = self.rect.topleft
        surface.blit(surf, draw_pos)

    def update(self, mouse_pos, mouse_pressed):
        was_hover = self._hovered
        self._hovered = self.rect.collidepoint(mouse_pos)
        clicked = False

        # play hover sound once when enter
        if self._hovered and not was_hover and hover_sound:
            try:
                hover_sound.play()
            except Exception:
                pass

        if self._hovered and mouse_pressed[0] and not self._pressed:
            self._pressed = True
        if not mouse_pressed[0] and self._pressed:
            if self._hovered:
                clicked = True
                # play click sound
                if click_sound:
                    try:
                        click_sound.play()
                    except Exception:
                        pass
            self._pressed = False
        return clicked


# desenhar painel semi-transparente
def draw_panel(surface, center_x, center_y, w, h, radius=18, color=(0, 0, 0, 140)):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, color, (0, 0, w, h), border_radius=radius)
    surface.blit(panel, (center_x - w // 2, center_y - h // 2))


# desenhar cobra (mantive sua implementação)
def desenhar_cobra(tela, cobra):
    for bloco in cobra:
        x, y, cor, forma = bloco
        if forma == "quadrado":
            pygame.draw.rect(tela, cor, [x, y, TAMANHO_BLOCO, TAMANHO_BLOCO])
        elif forma == "circulo":
            centro = (x + TAMANHO_BLOCO // 2, y + TAMANHO_BLOCO // 2)
            pygame.draw.circle(tela, cor, centro, TAMANHO_BLOCO // 2)
        elif forma == "triangulo":
            pontos = [
                (x + TAMANHO_BLOCO // 2, y),
                (x, y + TAMANHO_BLOCO),
                (x + TAMANHO_BLOCO, y + TAMANHO_BLOCO)
            ]
            pygame.draw.polygon(tela, cor, pontos)
        elif forma == "hexagono":
            r = TAMANHO_BLOCO // 2
            cx, cy = x + r, y + r
            pontos = [
                (cx + r * 0.866, cy - r * 0.5),
                (cx, cy - r),
                (cx - r * 0.866, cy - r * 0.5),
                (cx - r * 0.866, cy + r * 0.5),
                (cx, cy + r),
                (cx + r * 0.866, cy + r * 0.5),
            ]
            pygame.draw.polygon(tela, cor, pontos)


# --- Menus (com os botões bonitos) ---
def menu_principal():
    # painel central
    panel_w, panel_h = 560, 480
    panel_cx, panel_cy = LARGURA // 2, ALTURA // 2 - 40  # sobe um pouco

    # botões (criados uma vez ao entrar no menu)
    labels = ["JOGAR", "RECORDE", "OPÇÕES"]
    btn_w, btn_h = BOTAO_LARG, BOTAO_ALT
    spacing = 18
    start_y = panel_cy - 30 - (len(labels) * btn_h + (len(labels) - 1) * spacing) // 2
    buttons = []
    palette = [((70, 120, 255), (30, 40, 120)), ((240, 200, 60), (200, 120, 20)), ((0, 120, 180), (0, 80, 140))]

    for i, label in enumerate(labels):
        x = panel_cx - btn_w // 2
        y = start_y + i * (btn_h + spacing)
        topc, botc = palette[i]
        b = UIButton(label, (x, y, btn_w, btn_h), FONTE, topc, botc, icon_path=None)
        buttons.append(b)

    # botão sair/voltar no mesmo canto (canto inferior direito)
    margem = 30
    small_btn_rect = (LARGURA - 160 - margem, ALTURA - 50 - margem, 160, 50)
    btn_sair = UIButton("Sair", small_btn_rect, FONTE, (220, 70, 70), (160, 30, 30), icon_path=None, radius=12)

    pygame.mixer.music.stop()
    tocar_musica_menu()
    
    while True:
        # desenhar fundo
        if fundo:
            TELA.blit(fundo, (0, 0))
        else:
            TELA.fill((18, 18, 30))

        # desenhar painel
        draw_panel(TELA, panel_cx, panel_cy, panel_w, panel_h, radius=20, color=(0, 0, 0, 160))

        # Título
        titulo = FONTE_TITULO.render("SNAKE", True, BRANCO)
        TELA.blit(titulo, (panel_cx - titulo.get_width() // 2, panel_cy - panel_h // 2 + 24))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # atualizar e desenhar botões
        any_hover = False
        for b in buttons:
            if b.update(mouse_pos, mouse_pressed):
                if b.text == "JOGAR":
                    return "dificuldade"
                elif b.text == "RECORDE":
                    return "recordes"
                elif b.text == "OPÇÕES":
                    return "opcoes"
            b.draw(TELA)
            any_hover = any_hover or b._hovered

        if btn_sair.update(mouse_pos, mouse_pressed):
            # sair imediatamente
            sair_jogo()
        btn_sair.draw(TELA)
        any_hover = any_hover or btn_sair._hovered

        # cursor
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any_hover else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair_jogo()


def menu_dificuldade():
    panel_w, panel_h = 560, 360
    panel_cx, panel_cy = LARGURA // 2, ALTURA // 2 - 20

    btn_normal = UIButton("Normal", (panel_cx - BOTAO_LARG // 2, panel_cy - 40, BOTAO_LARG, BOTAO_ALT), FONTE, COR_BOTAO, COR_BOTAO_HOVER)
    btn_dificil = UIButton("Difícil", (panel_cx - BOTAO_LARG // 2, panel_cy + 40, BOTAO_LARG, BOTAO_ALT), FONTE, (200, 80, 80), (180, 40, 40))

    margem = 30
    btn_voltar = UIButton("Voltar", (LARGURA - 170 - margem, ALTURA - 50 - margem, 190, 50), FONTE, (0, 120, 180), (0, 90, 140))

    while True:
        if fundo:
            TELA.blit(fundo, (0, 0))
        else:
            TELA.fill((18, 18, 30))

        draw_panel(TELA, panel_cx, panel_cy, panel_w, panel_h, radius=18, color=(0, 0, 0, 160))
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        if btn_normal.update(mouse_pos, mouse_pressed):
            return "normal"
        if btn_dificil.update(mouse_pos, mouse_pressed):
            return "dificil"
        if btn_voltar.update(mouse_pos, mouse_pressed):
            return "menu"

        btn_normal.draw(TELA)
        btn_dificil.draw(TELA)
        btn_voltar.draw(TELA)

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if (btn_normal._hovered or btn_dificil._hovered or btn_voltar._hovered) else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair_jogo()


def tela_recordes():
    panel_w, panel_h = 560, 420
    panel_cx, panel_cy = LARGURA // 2, ALTURA // 2 - 20

    margem = 30
    btn_voltar = UIButton("Voltar", (LARGURA - 170 - margem, ALTURA - 50 - margem, 190, 50), FONTE, (0, 120, 180), (0, 90, 140))

    while True:
        if fundo:
            TELA.blit(fundo, (0, 0))
        else:
            TELA.fill((18, 18, 30))

        draw_panel(TELA, panel_cx, panel_cy, panel_w, panel_h, radius=18, color=(0, 0, 0, 160))

        titulo = FONTE_TITULO.render("Recordes", True, AMARELO)
        TELA.blit(titulo, (panel_cx - titulo.get_width() // 2, panel_cy - panel_h // 2 + 24))

        recorde_normal = carregar_recorde("normal")
        recorde_dificil = carregar_recorde("dificil")

        txt1 = FONTE.render(f"MODO NORMAL - {recorde_normal}", True, BRANCO)
        txt2 = FONTE.render(f"MODO DIFICIL - {recorde_dificil}", True, BRANCO)

        TELA.blit(txt1, (panel_cx - txt1.get_width() // 2, panel_cy - 20))
        TELA.blit(txt2, (panel_cx - txt2.get_width() // 2, panel_cy + 30))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        if btn_voltar.update(mouse_pos, mouse_pressed):
            return "menu"
        btn_voltar.draw(TELA)

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if btn_voltar._hovered else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair_jogo()

def menu_opcoes():
    global som_ativo, indice_cor_cobra, borda_ativa
    if not pygame.mixer.music.get_busy() and som_ativo:
        tocar_musica_menu()

    # Painel central
    panel_w, panel_h = 500, 500
    panel_x, panel_y = LARGURA // 2 - panel_w // 2, ALTURA // 2 - panel_h // 2

    # Botões (função auxiliar para recriar quando precisar atualizar)
    def criar_botoes():
        return {
            "som": UIButton(f"Som: {'ON' if som_ativo else 'OFF'}", (LARGURA // 2 - 150, panel_y + 120, 300, 60), FONTE, (70, 120, 255), (40, 80, 180)),
            "cor": UIButton("Cor", (LARGURA // 2 - 150, panel_y + 210, 300, 60), FONTE, (240, 200, 60), (200, 150, 30)),
            "borda": UIButton(f"Borda: {'ON' if borda_ativa else 'OFF'}", (LARGURA // 2 - 150, panel_y + 300, 300, 60), FONTE, (0, 200, 150), (0, 150, 100)),
        }

    botoes = criar_botoes() 

    botao_voltar = UIButton("Voltar", (LARGURA // 2 - 150, panel_y + 390, 300, 60), FONTE, (220, 70, 70), (160, 30, 30))

    while True:
        # Fundo
        if fundo:
            TELA.blit(fundo, (0, 0))
        else:
            TELA.fill((18, 18, 30))

        # Painel
        draw_panel(TELA, LARGURA // 2, ALTURA // 2, panel_w, panel_h, radius=20, color=(0, 0, 0, 180))

        # Título
        titulo = FONTE_TITULO.render("Opções", True, BRANCO)
        TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, panel_y + 30))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        any_hover = False

        # Atualizar botões
        for key, btn in botoes.items():
            if btn.update(mouse_pos, mouse_pressed):
                if key == "som":
                    som_ativo = not som_ativo
                    if som_ativo:
                        tocar_musica_menu()
                    else:
                        pygame.mixer.music.fadeout(300)
                    botoes = criar_botoes()  # recria para atualizar texto
                elif key == "cor":
                    indice_cor_cobra = (indice_cor_cobra + 1) % len(cores_cobra)
                elif key == "borda":
                    borda_ativa = not borda_ativa
                    botoes = criar_botoes()  # recria para atualizar texto
            btn.draw(TELA)
            any_hover = any_hover or btn._hovered

        # Quadrado da cor da cobra
        cor_atual = cores_cobra[indice_cor_cobra]
        pygame.draw.rect(TELA, cor_atual, (LARGURA // 2 + 100, panel_y + 220, 40, 40))

        # Botão voltar
        if botao_voltar.update(mouse_pos, mouse_pressed):
            return "menu"
        botao_voltar.draw(TELA)
        any_hover = any_hover or botao_voltar._hovered

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any_hover else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        clock.tick(60)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair_jogo()

# --- Função principal do jogo (mantive a lógica, só polimento visual)

def jogar(dificuldade="normal"):
    if dificuldade == "normal":
        velocidade = 7
    else:
        velocidade = 18
    
    pygame.mixer.music.stop()
    tocar_musica_jogo()

    modo = dificuldade
    recorde = carregar_recorde(modo)

    x = LARGURA // 2
    y = PAINEL_TOPO + (ALTURA_JOGO // 2)
    velocidade_x = 0
    velocidade_y = 0

    bombas = []
    corpo_cobra = []
    tamanho_cobra = 1

    tempo_inicio = pygame.time.get_ticks()
    comida_x, comida_y = gerar_comida()

    # música de fundo (se tiver)
    if os.path.exists(MUSICA):
        try:
            pygame.mixer.music.load(MUSICA)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    rodando = True
    while rodando:
        # --- eventos ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair_jogo()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT and velocidade_x == 0:
                    velocidade_x = -TAMANHO_BLOCO
                    velocidade_y = 0
                elif evento.key == pygame.K_RIGHT and velocidade_x == 0:
                    velocidade_x = TAMANHO_BLOCO
                    velocidade_y = 0
                elif evento.key == pygame.K_UP and velocidade_y == 0:
                    velocidade_y = -TAMANHO_BLOCO
                    velocidade_x = 0
                elif evento.key == pygame.K_DOWN and velocidade_y == 0:
                    velocidade_y = TAMANHO_BLOCO
                    velocidade_x = 0
                elif evento.key == pygame.K_ESCAPE:
                    rodando = False

        # --- mover cobra ---
        x += velocidade_x
        y += velocidade_y

        # --- paredes (borda) ---
        if borda_ativa:
          # parede mata
          if x < 0 or x >= LARGURA or y < PAINEL_TOPO or y >= ALTURA:
              tocar_sfx(som_gameover)
              rodando = False
        else:
             # sem borda: teletransporte (wrap)
             if x < 0:
                 x = LARGURA - TAMANHO_BLOCO
             elif x >= LARGURA:
                 x = 0
             if y < PAINEL_TOPO:
                 y = ALTURA - TAMANHO_BLOCO
             elif y >= ALTURA:
                 y = PAINEL_TOPO

        # atualizar cobra
        corpo_cobra.append([x, y, cor_aleatoria(), forma_aleatoria()])
        while len(corpo_cobra) > tamanho_cobra:
            corpo_cobra.pop(0)

        # colisão com corpo
        for parte in corpo_cobra[:-1]:
            if parte[0] == x and parte[1] == y:
                if som_gameover:
                    tocar_sfx(som_gameover)
                rodando = False

        # colisão com bombas
        for bomba_x, bomba_y in bombas:
            if x == bomba_x and y == bomba_y:
                if som_gameover:
                    tocar_sfx(som_gameover)
                rodando = False

        # colisão com comida
        if x == comida_x and y == comida_y:
            if som_comer:
                tocar_sfx(som_comer)
            tamanho_cobra += 1
            velocidade = min(velocidade + 0.5, 30)
            comida_x, comida_y = gerar_comida()

            # Regenerar bombas (modo difícil)
            if modo == "dificil":
                bombas.clear()
                num_bombas = max(1, tamanho_cobra // 2)
                for _ in range(num_bombas):
                    bx = random.randrange(0, LARGURA, TAMANHO_BLOCO)
                    by = random.randrange(PAINEL_TOPO, ALTURA, TAMANHO_BLOCO)
                    while (bx, by) == (comida_x, comida_y):
                        bx = random.randrange(0, LARGURA, TAMANHO_BLOCO)
                        by = random.randrange(PAINEL_TOPO, ALTURA, TAMANHO_BLOCO)
                    bombas.append((bx, by))

        # --- desenhar ---
        if fundo:
            TELA.blit(fundo, (0, 0))
        else:
            TELA.fill(PRETO)

        # painel superior (placar)
        # pygame.draw.rect(TELA, (30, 30, 30), (0, 0, LARGURA, PAINEL_TOPO))

        #linha divisoria
        pygame.draw.line(TELA, PRETO, (0, PAINEL_TOPO), (LARGURA, PAINEL_TOPO), 4)

        # desenhar comida
        pygame.draw.circle(TELA, BRANCO, (comida_x + TAMANHO_BLOCO // 2, comida_y + TAMANHO_BLOCO // 2), TAMANHO_BLOCO // 2 - 2)

        tempo_decorrido = (pygame.time.get_ticks() - tempo_inicio) // 1000

        # desenhar bombas como "X"
        offset = TAMANHO_BLOCO // 4
        for bomba_x, bomba_y in bombas:
            cor_bomba = (255, 0, 0)
            pygame.draw.line(TELA, cor_bomba, (bomba_x + offset, bomba_y + offset), (bomba_x + TAMANHO_BLOCO - offset, bomba_y + TAMANHO_BLOCO - offset), 3)
            pygame.draw.line(TELA, cor_bomba, (bomba_x + TAMANHO_BLOCO - offset, bomba_y + offset), (bomba_x + offset, bomba_y + TAMANHO_BLOCO - offset), 3)

        # desenhar cobra
        desenhar_cobra(TELA, corpo_cobra)

        # Placar com imagens
        pontos = tamanho_cobra - 1

        # Troféu (pontuação)
        TELA.blit(img_trofeu, (30, 7))  # desenha o troféu
        pontos_txt = FONTE.render(f"{pontos}", True, BRANCO)
        TELA.blit(pontos_txt, (80, 10))  # valor ao lado do troféu

        # Ampulheta (tempo)
        TELA.blit(img_ampulheta, (LARGURA - 190, 2))  # desenha a ampulheta
        tempo_txt = FONTE.render(f"{tempo_decorrido}s", True, AMARELO)
        TELA.blit(tempo_txt, (LARGURA - 130, 10))  # valor ao lado da ampulheta

        pygame.display.update()
        clock.tick(velocidade)

        # recorde
        recorde = carregar_recorde(modo)
        if pontos > recorde:
            salvar_recorde(modo, pontos)

    # --- game over ---
    pygame.mixer.music.fadeout(300)
    return "menu"


# --- utilitarios ---
def sair_jogo():
    try:
        pygame.mixer.music.stop()
    except:
        pass
    pygame.quit()
    sys.exit()

# --- Loop principal ---
if __name__ == "__main__":
    estado = "menu"
    while True:
        if estado == "menu":
            estado = menu_principal()

        elif estado == "dificuldade":
            escolha = menu_dificuldade()
            if escolha in ("normal", "dificil"):
                estado = jogar(escolha)
            else:
                estado = escolha

        elif estado == "recordes":
            estado = tela_recordes()

        elif estado == "opcoes":
            estado = menu_opcoes() or "menu"

        else:
            estado = "menu"
