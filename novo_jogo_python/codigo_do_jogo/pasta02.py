# Codigo d jogo Rogalike
import math, random  # Importa módulos para operações matemáticas
from pgzero.builtins import Actor, Rect, keyboard, screen, music, sound, keys, clock  # Importacao componentes específicos do PgZero
#Constants
WIDTH, HEIGHT = 640, 480  #largura
TITLE = "Micro Roguelike"   # Título
TILE_SIZE = 32

# Controla acontecimentos no jogo
GAME_STATE_MENU, GAME_STATE_PLAYING, GAME_STATE_GAME_OVER = 0, 1, 2
current_game_state = GAME_STATE_MENU
# cores
WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (200, 0, 0)

MAP_WIDTH, MAP_HEIGHT = WIDTH // TILE_SIZE, HEIGHT // TILE_SIZE  # Dimensoes
#Variaveis globais
game_map = []
player_turn = True
music_enabled = True
sound_enabled = True

# Classe Objetos do jogo... Heroi e inimigo
class GameObject:
    def __init__(self, x, y, img_prefix, anim_frames, anim_speed=0.2):
        self.x, self.y = x, y
        self.actor = Actor(f"{img_prefix}_idle_1")
        self.actor.pos = (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
        self.img_prefix = img_prefix
        self.anim_frames = anim_frames
        self.current_anim = 'idle'
        self.frame_idx, self.anim_timer = 0, 0.0
        self.anim_speed = anim_speed
        self.is_alive = True

    #Atualiza o frame atual e animação de objeto.
    def update_animation(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0.0
            frames = self.anim_frames.get(self.current_anim, [])
            if frames: self.actor.image = f"{self.img_prefix}_{frames[(self.frame_idx + 1) % len(frames)]}"; self.frame_idx = (self.frame_idx + 1) % len(frames)
            else: self.actor.image = f"{self.img_prefix}_idle_1"
    #Dezenha o personagem na tela
    def draw(self): self.actor.draw()

    def move_to_tile(self, new_x, new_y):
        #Move o objeto
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and game_map[new_y][new_x] == '.':
            self.x, self.y = new_x, new_y
            self.actor.pos = (new_x * TILE_SIZE + TILE_SIZE // 2, new_y * TILE_SIZE + TILE_SIZE // 2)
            self.current_anim = 'walk'
            return True  # Se movomento sucesido...Return True
        self.current_anim = 'idle'  # Se nao mover retorna...
        return False
#Classe jogador
class Player(GameObject):
    def __init__(self, x, y):
        # Chama o construtor da classe base
        super().__init__(x, y, "player", {'idle': ['idle_1', 'idle_2'], 'walk': ['walk_1', 'walk_2']})
        self.hp, self.attack_power = 100, 15  # Poder de ataque...(jogador)

    def take_damage(self, amount):
        # Se HP <= 0, o jogo termina...
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            global current_game_state # modifica a variavel global
            current_game_state = GAME_STATE_GAME_OVER
            music.stop()  # Para a música de fundo
    def attack(self, target_enemy):
        #O jogador ataca um alvo inimigo...
        if sound_enabled: sound.play('player_attack');
        target_enemy.take_damage(self.attack_power) # Machuca o nimigo
    def set_animation_state(self, is_moving): self.current_anim = 'walk' if is_moving else 'idle'

# Classe do Inimigo - herda da GameObject
class Enemy(GameObject):
    #Chama o construtor da classe...
    def __init__(self, x, y):
        super().__init__(x, y, "enemy", {'idle': ['idle_1', 'idle_2'], 'walk': ['walk_1', 'walk_2']})
        self.hp, self.attack_power = 50, 10  # poder de ataque do inimigo
        self.current_anim = 'walk'

    def take_damage(self, amount):
        #Se HP <= 0, entao inimigo não está mais vivo
        self.hp -= amount
        if sound_enabled: sound.play('enemy_hit');  #toca som
        if self.hp <= 0: self.hp = 0; self.is_alive = False
    def attack(self, target_player):
        #Inimigo ataca o alvo...
        if sound_enabled: sound.play('enemy_attack'); #  som de ataque se habilitado.
        target_player.take_damage(self.attack_power)
    def ai_move(self, player_obj):
        #IA simples para o movimento do inimigo
        if not self.is_alive: return
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        if self.move_to_tile(self.x + dx, self.y + dy): self.set_animation_state(True)
        else: self.set_animation_state(False)
    def set_animation_state(self, is_moving): self.current_anim = 'walk' if is_moving else 'idle'

player, enemies = None, []  # Instâncias de Objetos do Jogo
# Mapa gerar...
def generate_map():
    global game_map
    game_map = [['.' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    for _ in range(MAP_WIDTH * MAP_HEIGHT // 15):
        wx, wy = random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1)
        game_map[wy][wx] = '#'
    px, py = MAP_WIDTH // 4, MAP_HEIGHT // 2; game_map[py][px] = '.'; return px, py
#  Inicializa o jogo...
def init_game():
    #Inicializa uma nova partida.
    global player, enemies, player_turn, current_game_state
    current_game_state = GAME_STATE_PLAYING  # muda estado para Jogando...
    px, py = generate_map(); player = Player(px, py); enemies = []
    for _ in range(random.randint(1, 3)): # cria qntidd de inimigo ate 3...
        ex, ey = random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1)
        while (ex == player.x and ey == player.y) or game_map[ey][ex] == '#':
            ex, ey = random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1)
        enemies.append(Enemy(ex, ey))
    player_turn = True
    if music_enabled: music.play('background_music')  # tocando musica de fundo...
# Menu---para ação
#inicia o jogo
def start_game_action(): init_game()
def toggle_music_sound_action():
    global music_enabled, sound_enabled # Declare global before modifying
    music_enabled = not music_enabled; sound_enabled = not sound_enabled
    if music_enabled: music.unpause(); music.set_volume(0.5)
    else: music.pause(); music.set_volume(0.0)
    #sai do pgZero...
def exit_game_action(): exit()

def draw():
    screen.fill(BLACK)  #preenche o fundo da ela
    if current_game_state == GAME_STATE_MENU:
        #texto dos botoes..
        screen.draw.text(TITLE, center=(WIDTH / 2, HEIGHT / 4), color=WHITE, fontsize=70)
        screen.draw.text("Start Game", center=(WIDTH/2, HEIGHT/2 - 40), color=WHITE, fontsize=40)
        screen.draw.text("Music/Sound", center=(WIDTH/2, HEIGHT/2 + 20), color=WHITE, fontsize=40)
        screen.draw.text("Exit", center=(WIDTH/2, HEIGHT/2 + 80), color=WHITE, fontsize=40)
    elif current_game_state == GAME_STATE_PLAYING:
       #chão e paredes
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH): screen.blit('wall' if game_map[y][x] == '#' else 'floor', (x * TILE_SIZE, y * TILE_SIZE))
        player.draw(); [e.draw() for e in enemies if e.is_alive]
        screen.draw.text(f"HP: {player.hp}", topleft=(10, 10), color=RED, fontsize=30)
        screen.draw.text(f"Turn: {'Player' if player_turn else 'Enemy'}", topleft=(10, 40), color=WHITE, fontsize=20)
    elif current_game_state == GAME_STATE_GAME_OVER:
        screen.draw.text("GAME OVER", center=(WIDTH / 2, HEIGHT / 2 - 20), color=RED, fontsize=80)
        screen.draw.text("Press R to Restart", center=(WIDTH / 2, HEIGHT / 2 + 30), color=WHITE, fontsize=30)

def update(dt):
    #atualização do PgZero, chamada automaticamente a cada frame para a lógica do jogo.
    if current_game_state == GAME_STATE_PLAYING:
        player.update_animation(dt); [e.update_animation(dt) for e in enemies]
        global enemies   # modificar a variável global 'enemies'.
        enemies = [e for e in enemies if e.is_alive]
        if not player.is_alive:
            global current_game_state
            current_game_state = GAME_STATE_GAME_OVER
            music.stop() # para a musica

def on_key_down(key):
    #pressionar de teclas para movimento e ações do jogador...
    global player_turn, current_game_state # modificar var...Globais
    if current_game_state == GAME_STATE_PLAYING and player_turn:
        dx, dy = 0, 0   # deslocamento nas coordenadas x e y.
        if key == keys.LEFT: dx = -1
        elif key == keys.RIGHT: dx = 1
        elif key == keys.UP: dy = -1
        elif key == keys.DOWN: dy = 1
        if dx != 0 or dy != 0:
            tx, ty = player.x + dx, player.y + dy
            enemy_on_tile = next((e for e in enemies if e.x == tx and e.y == ty and e.is_alive), None)
            if enemy_on_tile: player.attack(enemy_on_tile); player.set_animation_state(False); player_turn = False; clock.schedule_unique(enemy_turns, 0.3)
            elif player.move_to_tile(tx, ty): player.set_animation_state(True); player_turn = False; clock.schedule_unique(enemy_turns, 0.3)
            else: player.set_animation_state(False)
        else: player.set_animation_state(False)
    elif current_game_state == GAME_STATE_GAME_OVER and key == keys.R: init_game()  # Inicializa  deslocamento nas coordenadas x e y...

def on_mouse_down(pos):
    #botões do menu.
    global current_game_state # modificar variavel global
    if current_game_state == GAME_STATE_MENU:  # se o jogo estiver no menu, mostrar...
        if Rect(WIDTH/2 - 100, HEIGHT/2 - 60, 200, 40).collidepoint(pos): start_game_action() #start
        elif Rect(WIDTH/2 - 100, HEIGHT/2, 200, 40).collidepoint(pos): toggle_music_sound_action()  #som
        elif Rect(WIDTH/2 - 100, HEIGHT/2 + 60, 200, 40).collidepoint(pos): exit_game_action()  #sair
def enemy_turns():
    #Executa ações dos inimigos - movimento e ataque
    global player_turn # Declare global before modifying
    for enemy in enemies:   # Iteracao de cada inimigo na lista...
        if enemy.is_alive:
            enemy.ai_move(player)
            if abs(player.x - enemy.x) <= 1 and abs(player.y - enemy.y) <= 1 and player.is_alive: enemy.attack(player)
            enemy.set_animation_state(False)
            if not player.is_alive: break   # Se o jogador morrer, interrompe o loop.
    player_turn = True
