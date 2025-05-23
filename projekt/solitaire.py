import pygame
import sys
import os
import random
from pathlib import Path

#inicjalizacja pygame
pygame.init()

#pobranie informacji o ekranie
screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

#ustawienia wymiarow kart i odstepow
CARD_WIDTH = int(WINDOW_WIDTH * 0.08)    
CARD_HEIGHT = int(CARD_WIDTH * 1.4)    
CARD_SPACING = int(CARD_WIDTH * 0.3)    
PILE_SPACING = int(CARD_WIDTH * 0.2)     
FPS = 60

#definicja kolorow
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
BLACK = (0, 0, 0)

#utworzenie okna gry
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Solitaire")
clock = pygame.time.Clock()

#wczytanie tla i tylu karty
background = pygame.image.load(os.path.join('assets', 'background.jpg'))
background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
card_back = pygame.image.load(os.path.join('assets', 'cardback.png'))
card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))

class Card:
    def __init__(self, suit, value):
        self.suit = suit  #kolor karty
        self.value = value  #wartosc karty
        self.face_up = False  #czy karta jest odkryta
        self.image = None
        self.rect = None
        self.load_image()
        
    def load_image(self):
        #mapowanie wartosci kart na symbole
        value_map = {
            1: 'A',   #As
            10: 'T',  #10
            11: 'J',  #Walet
            12: 'Q',  #Dama
            13: 'K'   #Krol
        }
        value_str = value_map.get(self.value, str(self.value))
        
        #mapowanie kolorow kart na symbole
        suit_map = {
            'hearts': 'H',    #Kiery
            'diamonds': 'D',  #Karo
            'clubs': 'C',     #Trefl
            'spades': 'S'     #Pik
        }
        suit_str = suit_map[self.suit]
        
        #wczytanie obrazu karty
        image_path = os.path.join('assets', 'cards', 'png', f'{value_str}{suit_str}.png')
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (CARD_WIDTH, CARD_HEIGHT))
        self.rect = self.image.get_rect()

    def draw(self, surface, x, y):
        #rysowanie karty na planszy
        self.rect.x = x
        self.rect.y = y
        if self.face_up:
            surface.blit(self.image, self.rect)
        else:
            surface.blit(card_back, self.rect)

class Deck:
    def __init__(self):
        self.cards = []
        self.create_deck()
        
    def create_deck(self):
        #tworzenie talii kart
        suits = ['hearts', 'diamonds', 'clubs', 'spades'] 
        for suit in suits:
            for value in range(1, 14):  
                self.cards.append(Card(suit, value))
                
    def shuffle(self):
        #tasowanie kart
        random.shuffle(self.cards)
        
    def deal(self):
        #rozdawanie kart
        if self.cards:
            return self.cards.pop()
        return None

class GameBoard:
    def __init__(self):
        self.tableau_piles = [[] for _ in range(7)]  #7 stosow glownych
        self.foundation_piles = [[] for _ in range(4)]  #4 stosy docelowe
        self.stock_pile = []  #stos kart do dobierania
        self.waste_pile = []  #stos odrzuconych kart
        
    def deal_initial_cards(self, deck):
        #rozdanie poczatkowych kart do stosow
        for i in range(7):
            for j in range(i + 1):
                card = deck.deal()
                if j == i:
                    card.face_up = True
                self.tableau_piles[i].append(card)
        
        #reszta kart idzie do stosu dobierania
        while deck.cards:
            self.stock_pile.append(deck.deal())
            
    def draw(self, surface):
        #obliczenie pozycji startowej dla stosow glownych
        total_tableau_width = 7 * (CARD_WIDTH + PILE_SPACING) - PILE_SPACING
        start_x = (WINDOW_WIDTH - total_tableau_width) // 2
        
        #rysowanie stosow glownych
        for i, pile in enumerate(self.tableau_piles):
            x = start_x + i * (CARD_WIDTH + PILE_SPACING)
            for j, card in enumerate(pile):
                y = int(WINDOW_HEIGHT * 0.3) + j * CARD_SPACING
                card.draw(surface, x, y)
        
        #rysowanie stosow docelowych
        foundation_start_x = int(WINDOW_WIDTH * 0.1)
        for i, pile in enumerate(self.foundation_piles):
            x = foundation_start_x + i * (CARD_WIDTH + PILE_SPACING)
            if pile:
                pile[-1].draw(surface, x, int(WINDOW_HEIGHT * 0.05))
            else:
                pygame.draw.rect(surface, WHITE, (x, int(WINDOW_HEIGHT * 0.05), CARD_WIDTH, CARD_HEIGHT), 2)
        
        #rysowanie stosu dobierania
        stock_x = int(WINDOW_WIDTH * 0.8)
        if self.stock_pile:
            self.stock_pile[-1].draw(surface, stock_x, int(WINDOW_HEIGHT * 0.05))
        else:
            pygame.draw.rect(surface, WHITE, (stock_x, int(WINDOW_HEIGHT * 0.05), CARD_WIDTH, CARD_HEIGHT), 2)
        
        #rysowanie stosu odrzuconych kart
        waste_x = stock_x - CARD_WIDTH - PILE_SPACING
        if self.waste_pile:
            self.waste_pile[-1].draw(surface, waste_x, int(WINDOW_HEIGHT * 0.05))
        else:
            pygame.draw.rect(surface, WHITE, (waste_x, int(WINDOW_HEIGHT * 0.05), CARD_WIDTH, CARD_HEIGHT), 2)


def is_opposite_color(card1, card2):
    #sprawdzenie czy karty sa przeciwnego koloru
    red = ['hearts', 'diamonds']
    black = ['spades', 'clubs']
    return ((card1.suit in red and card2.suit in black) or
            (card1.suit in black and card2.suit in red))

def can_move_to_foundation(card, pile):
    #sprawdzenie czy karte mozna polozyc na stos docelowy
    if not pile:
        return card.value == 1  #as
    top = pile[-1]
    return card.suit == top.suit and card.value == top.value + 1


def serialize_pile(pile):
    #konwersja stosu kart na format do zapisu
    return [(card.suit, card.value, card.face_up) for card in pile]

def serialize_game_board(game_board, picked_cards, picked_from):
    #zapisanie calego stanu gry
    tableau_copy = [pile[:] for pile in game_board.tableau_piles]
    if picked_cards and picked_from and picked_from[0] == 'tableau':
        src_i, src_j = picked_from[1], picked_from[2]
        tableau_copy[src_i] = tableau_copy[src_i][:src_j] + picked_cards
    return {
        'tableau_piles': [serialize_pile(pile) for pile in tableau_copy],
        'foundation_piles': [serialize_pile(pile) for pile in game_board.foundation_piles],
        'stock_pile': serialize_pile(game_board.stock_pile),
        'waste_pile': serialize_pile(game_board.waste_pile),
        'picked_cards': [],
        'picked_from': None
    }

def deserialize_game_board(data):
    #wczytanie stanu gry
    gb = GameBoard()
    gb.tableau_piles = []
    for pile_data in data['tableau_piles']:
        pile = []
        for suit, value, face_up in pile_data:
            c = Card(suit, value)
            c.face_up = face_up
            pile.append(c)
        gb.tableau_piles.append(pile)
    gb.foundation_piles = []
    for pile_data in data['foundation_piles']:
        pile = []
        for suit, value, face_up in pile_data:
            c = Card(suit, value)
            c.face_up = face_up
            pile.append(c)
        gb.foundation_piles.append(pile)
    gb.stock_pile = []
    for suit, value, face_up in data['stock_pile']:
        c = Card(suit, value)
        c.face_up = face_up
        gb.stock_pile.append(c)
    gb.waste_pile = []
    for suit, value, face_up in data['waste_pile']:
        c = Card(suit, value)
        c.face_up = face_up
        gb.waste_pile.append(c)
    picked_cards = []
    picked_from = None
    return gb, picked_cards, picked_from

def draw_menu(screen, font, WINDOW_WIDTH, WINDOW_HEIGHT):
    screen.fill((0, 128, 0))
    title_font = pygame.font.SysFont(None, 80)
    title = title_font.render('Solitaire', True, (255, 255, 255))
    title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 6))
    screen.blit(title, title_rect)

    label_font = pygame.font.SysFont(None, 40)
    label = label_font.render('Difficulty level:', True, (255, 255, 255))
    label_rect = label.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
    screen.blit(label, label_rect)
    button_font = pygame.font.SysFont(None, 48)
    buttons = [
        ('Beginner', (0, 200, 0)),
        ('Medium', (200, 200, 0)),
        ('Expert', (200, 0, 0)),
    ]
    button_rects = []
    for i, (label, color) in enumerate(buttons):
        rect = pygame.Rect(WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 3 + 50 + i * 80, 240, 60)
        pygame.draw.rect(screen, color, rect)
        text = button_font.render(label, True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        button_rects.append(rect)
    pygame.display.flip()
    return button_rects

def is_game_won(game_board):
    return all(len(pile) == 13 for pile in game_board.foundation_piles)

def all_tableau_face_up(game_board):
    for pile in game_board.tableau_piles:
        for card in pile:
            if not card.face_up:
                return False
    return True

def main():

    deck = Deck()
    deck.shuffle()
    game_board = GameBoard()
    game_board.deal_initial_cards(deck)

    picked_cards = []
    picked_from = None
    history = [] 
    font = pygame.font.SysFont(None, 36)
    game_state = 'menu' 
    difficulty = None
    running = True
    game_won = False
    start_ticks = pygame.time.get_ticks()
    final_time = None

    while running:
        if game_state == 'menu':
            button_rects = draw_menu(screen, font, WINDOW_WIDTH, WINDOW_HEIGHT)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                  
                    #wybor poziomu trudnosci
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(mouse_x, mouse_y):
                            if i == 0:
                                difficulty = 'beginner'
                            elif i == 1:
                                difficulty = 'medium'
                            elif i == 2:
                                difficulty = 'expert'
                            #reset gry po wyborze poziomu
                            deck = Deck()
                            deck.shuffle()
                            game_board = GameBoard()
                            game_board.deal_initial_cards(deck)
                            picked_cards = []
                            picked_from = None
                            history = []
                            start_ticks = pygame.time.get_ticks()
                            final_time = None
                            game_state = 'playing'
                            break
            continue

        #obsluga zdarzen w grze
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                #przycisk nowej gry
                newgame_rect = pygame.Rect(20, WINDOW_HEIGHT - 70, 140, 50)
                if newgame_rect.collidepoint(mouse_x, mouse_y):
                    deck = Deck()
                    deck.shuffle()
                    game_board = GameBoard()
                    game_board.deal_initial_cards(deck)
                    picked_cards = []
                    picked_from = None
                    history = []
                    start_ticks = pygame.time.get_ticks()
                    final_time = None
                    continue

                #przycisk cofnij ruch
                if difficulty != 'expert':
                    return_rect = pygame.Rect(WINDOW_WIDTH - 160, 20, 140, 50)
                    if return_rect.collidepoint(mouse_x, mouse_y):
                        if history:
                            game_board, picked_cards, picked_from = deserialize_game_board(history.pop())
                        continue

                #przycisk powrotu do menu
                if game_state == 'playing':
                    return_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT - 100, 160, 60)
                    if return_menu_rect.collidepoint(mouse_x, mouse_y):
                        game_state = 'menu'
                        continue

                #zapisanie stanu gry przed ruchem
                if not picked_cards and difficulty != 'expert':
                    history.append(serialize_game_board(game_board, picked_cards, picked_from))

               
                if picked_cards:
                    #proba polozenia karty na stos docelowy
                    foundation_start_x = int(WINDOW_WIDTH * 0.1)
                    for i, pile in enumerate(game_board.foundation_piles):
                        pile_x = foundation_start_x + i * (CARD_WIDTH + PILE_SPACING)
                        pile_rect = pygame.Rect(pile_x, int(WINDOW_HEIGHT * 0.05), CARD_WIDTH, CARD_HEIGHT)
                        if pile_rect.collidepoint(mouse_x, mouse_y):
                            if can_move_to_foundation(picked_cards[0], pile):
                                pile.extend(picked_cards)
                                if picked_from[0] == 'waste':
                                    pass  
                                elif picked_from[0] == 'tableau':
                                    game_board.tableau_piles[picked_from[1]] = game_board.tableau_piles[picked_from[1]][:picked_from[2]]
                                    if game_board.tableau_piles[picked_from[1]] and not game_board.tableau_piles[picked_from[1]][-1].face_up:
                                        game_board.tableau_piles[picked_from[1]][-1].face_up = True
                                picked_cards = []
                                picked_from = None
                                break

                    #proba polozenia karty na stos glowny
                    if picked_cards:
                        total_tableau_width = 7 * (CARD_WIDTH + PILE_SPACING) - PILE_SPACING
                        tableau_start_x = (WINDOW_WIDTH - total_tableau_width) // 2
                        for i, pile in enumerate(game_board.tableau_piles):
                            x = tableau_start_x + i * (CARD_WIDTH + PILE_SPACING)
                            y = int(WINDOW_HEIGHT * 0.3)
                            pile_clicked = False
                            for j, card in enumerate(pile):
                                card_y = y + j * CARD_SPACING
                                
                                #sprawdzenie klikniecia na karte
                                if j < len(pile) - 1:
                                    rect = pygame.Rect(x, card_y, CARD_WIDTH, CARD_SPACING)
                                else:
                                    rect = pygame.Rect(x, card_y, CARD_WIDTH, CARD_HEIGHT)
                                if card.face_up and rect.collidepoint(mouse_x, mouse_y):
                                    if pile:
                                        top_card = pile[-1]
                                        if is_opposite_color(picked_cards[0], top_card) and picked_cards[0].value == top_card.value - 1:
                                            pile.extend(picked_cards)
                                            if picked_from[0] == 'waste':
                                                pass  
                                            elif picked_from[0] == 'tableau':
                                                game_board.tableau_piles[picked_from[1]] = game_board.tableau_piles[picked_from[1]][:picked_from[2]]
                                                if game_board.tableau_piles[picked_from[1]] and not game_board.tableau_piles[picked_from[1]][-1].face_up:
                                                    game_board.tableau_piles[picked_from[1]][-1].face_up = True
                                            picked_cards = []
                                            picked_from = None
                                            pile_clicked = True
                                            break
                                    else:
                                        if picked_cards[0].value == 13:
                                            pile.extend(picked_cards)
                                            if picked_from[0] == 'waste':
                                                pass 
                                            elif picked_from[0] == 'tableau':
                                                game_board.tableau_piles[picked_from[1]] = game_board.tableau_piles[picked_from[1]][:picked_from[2]]
                                                if game_board.tableau_piles[picked_from[1]] and not game_board.tableau_piles[picked_from[1]][-1].face_up:
                                                    game_board.tableau_piles[picked_from[1]][-1].face_up = True
                                            picked_cards = []
                                            picked_from = None
                                            pile_clicked = True
                                            break
                           
                            #sprawdzenie klikniecia na pusty stos
                            if not pile and not pile_clicked:
                                empty_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                                if empty_rect.collidepoint(mouse_x, mouse_y):
                                    if picked_cards[0].value == 13:
                                        pile.extend(picked_cards)
                                        if picked_from[0] == 'waste':
                                            pass  
                                        elif picked_from[0] == 'tableau':
                                            game_board.tableau_piles[picked_from[1]] = game_board.tableau_piles[picked_from[1]][:picked_from[2]]
                                            if game_board.tableau_piles[picked_from[1]] and not game_board.tableau_piles[picked_from[1]][-1].face_up:
                                                game_board.tableau_piles[picked_from[1]][-1].face_up = True
                                        picked_cards = []
                                        picked_from = None
                                        break
                            if not picked_cards:
                                break

                    #zwrocenie kart na miejsce startowe
                    if picked_cards:
                        if picked_from[0] == 'waste':
                            picked_cards[0].face_up = True
                            game_board.waste_pile.append(picked_cards[0])
                        elif picked_from[0] == 'tableau':
                            game_board.tableau_piles[picked_from[1]].extend(picked_cards)
                        elif picked_from[0] == 'foundation':
                            game_board.foundation_piles[picked_from[1]].extend(picked_cards)
                        picked_cards = []
                        picked_from = None

                else:
                    #obsluga klikniecia na stos dobierania i odrzuconych kart
                    stock_x = int(WINDOW_WIDTH * 0.8)
                    stock_y = int(WINDOW_HEIGHT * 0.05)
                    stock_rect = pygame.Rect(stock_x, stock_y, CARD_WIDTH, CARD_HEIGHT)
                    waste_x = stock_x - CARD_WIDTH - PILE_SPACING
                    waste_y = stock_y
                    waste_rect = pygame.Rect(waste_x, waste_y, CARD_WIDTH, CARD_HEIGHT)

                    #klikniecie na stos odrzuconych kart
                    if waste_rect.collidepoint(mouse_x, mouse_y) and game_board.waste_pile:
                        picked_cards = [game_board.waste_pile.pop()]
                        picked_from = ('waste', None)
                        continue
                    
                    #klikniecie na stos dobierania
                    if stock_rect.collidepoint(mouse_x, mouse_y):
                        waste_x = stock_x - CARD_WIDTH - PILE_SPACING
                        waste_y = stock_y
                        waste_rect = pygame.Rect(waste_x, waste_y, CARD_WIDTH, CARD_HEIGHT)
                        if waste_rect.collidepoint(mouse_x, mouse_y) and game_board.waste_pile:
                            picked_cards = [game_board.waste_pile.pop()]
                            picked_from = ('waste', None)
                            continue
                        if game_board.stock_pile:
                            card = game_board.stock_pile.pop()
                            card.face_up = True
                            game_board.waste_pile.append(card)
                            picked_cards = []
                            picked_from = None
                        else:
                            #przeniesienie kart ze stosu odrzuconych z powrotem do dobierania
                            while game_board.waste_pile:
                                card = game_board.waste_pile.pop()
                                card.face_up = False
                                game_board.stock_pile.append(card)
                            picked_cards = []
                            picked_from = None
                        continue

                    #obsluga klikniecia na karty w stosach docelowych (tylko w trybie beginner)
                    if not picked_cards and difficulty == 'beginner':
                        foundation_start_x = int(WINDOW_WIDTH * 0.1)
                        for i, pile in enumerate(game_board.foundation_piles):
                            if pile:
                                x = foundation_start_x + i * (CARD_WIDTH + PILE_SPACING)
                                y = int(WINDOW_HEIGHT * 0.05)
                                rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                                if rect.collidepoint(mouse_x, mouse_y):
                                    picked_cards = [pile.pop()]
                                    picked_from = ('foundation', i)
                                    break

                    #obsluga klikniecia na karty w stosach glownych
                    if not picked_cards:
                        total_tableau_width = 7 * (CARD_WIDTH + PILE_SPACING) - PILE_SPACING
                        tableau_start_x = (WINDOW_WIDTH - total_tableau_width) // 2
                        for i, pile in enumerate(game_board.tableau_piles):
                            x = tableau_start_x + i * (CARD_WIDTH + PILE_SPACING)
                            y = int(WINDOW_HEIGHT * 0.3)
                            for j, card in enumerate(pile):
                                card_y = y + j * CARD_SPACING
                               
                                #sprawdzenie klikniecia na karte
                                if j < len(pile) - 1:
                                    rect = pygame.Rect(x, card_y, CARD_WIDTH, CARD_SPACING)
                                else:
                                    rect = pygame.Rect(x, card_y, CARD_WIDTH, CARD_HEIGHT)
                                if card.face_up and rect.collidepoint(mouse_x, mouse_y):
                                    picked_cards = pile[j:]
                                    picked_from = ('tableau', i, j)
                                    game_board.tableau_piles[i] = pile[:j]
                                    break
                            if picked_cards:
                                break

                #obsluga przycisku auto-finish
                if 'autofinish_rect' in locals() and autofinish_rect and autofinish_rect.collidepoint(mouse_x, mouse_y):
                    moved = True
                    while moved:
                        moved = False
                  
                        #proba przeniesienia kart ze stosow glownych
                        for pile in game_board.tableau_piles:
                            if pile:
                                card = pile[-1]
                                for f_pile in game_board.foundation_piles:
                                    if can_move_to_foundation(card, f_pile):
                                        f_pile.append(pile.pop())
                                        moved = True
                                        break
             
                        #proba przeniesienia karty ze stosu odrzuconych
                        if game_board.waste_pile:
                            card = game_board.waste_pile[-1]
                            for f_pile in game_board.foundation_piles:
                                if can_move_to_foundation(card, f_pile):
                                    f_pile.append(game_board.waste_pile.pop())
                                    moved = True
                                    break
                    continue

        screen.blit(background, (0, 0))
        game_board.draw(screen)

        newgame_rect = pygame.Rect(20, WINDOW_HEIGHT - 70, 140, 50)
        pygame.draw.rect(screen, (200, 200, 200), newgame_rect)
        text = font.render('New Game', True, (0, 0, 0))
        text_rect = text.get_rect(center=newgame_rect.center)
        screen.blit(text, text_rect)
  
        #wyswietlanie timera
        if not game_won:
            timer_font = pygame.font.SysFont(None, 36)
            elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
            minutes = elapsed // 60
            seconds = elapsed % 60
            timer_text = timer_font.render(f"Time: {minutes:02}:{seconds:02}", True, (255, 255, 255))
            screen.blit(timer_text, (20, WINDOW_HEIGHT - 140))

        #wyswietlanie poziomu trudnosci
        if difficulty:
            diff_label = font.render(f'Level: {difficulty.capitalize()}', True, (255, 255, 255))
            screen.blit(diff_label, (20, WINDOW_HEIGHT - 110))

        #rysowanie przycisku cofnij ruch
        if difficulty != 'expert':
            return_rect = pygame.Rect(WINDOW_WIDTH - 160, 20, 140, 50)
            pygame.draw.rect(screen, (200, 200, 200), return_rect)
            text = font.render('Undo', True, (0, 0, 0))
            text_rect = text.get_rect(center=return_rect.center)
            screen.blit(text, text_rect)
     
        #rysowanie przycisku powrotu do menu
        if game_state == 'playing':
            return_menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT - 100, 160, 60)
            pygame.draw.rect(screen, (180, 180, 180), return_menu_rect)
            return_menu_text = font.render('Return', True, (0, 0, 0))
            return_menu_text_rect = return_menu_text.get_rect(center=return_menu_rect.center)
            screen.blit(return_menu_text, return_menu_text_rect)

        #wyswietlanie przycisku auto-finish
        show_autofinish = all_tableau_face_up(game_board) and not game_won
        autofinish_rect = None
        if show_autofinish:
            autofinish_width = 400
            autofinish_height = 70
            autofinish_x = (WINDOW_WIDTH - autofinish_width) // 2
            autofinish_y = WINDOW_HEIGHT - 230
            autofinish_rect = pygame.Rect(autofinish_x, autofinish_y, autofinish_width, autofinish_height)
            pygame.draw.rect(screen, (180, 220, 180), autofinish_rect, border_radius=20)
            big_font = pygame.font.SysFont(None, 60)
            autofinish_text = big_font.render('AUTO-FINISH', True, (0, 0, 0))
            autofinish_text_rect = autofinish_text.get_rect(center=autofinish_rect.center)
            screen.blit(autofinish_text, autofinish_text_rect)

        #rysowanie podnoszonych kart
        if picked_cards:
            mx, my = pygame.mouse.get_pos()
     
            #podswietlanie mozliwych miejsc docelowych
            if len(picked_cards) == 1:
                foundation_start_x = int(WINDOW_WIDTH * 0.1)
                for i, pile in enumerate(game_board.foundation_piles):
                    x = foundation_start_x + i * (CARD_WIDTH + PILE_SPACING)
                    y = int(WINDOW_HEIGHT * 0.05)
                    pile_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                    if can_move_to_foundation(picked_cards[0], pile):
                        pygame.draw.rect(screen, (255, 215, 0), pile_rect, 4) 
            #rysowanie podnoszonych kart
            for idx, card in enumerate(picked_cards):
                card.draw(screen, mx - CARD_WIDTH // 2, my - CARD_HEIGHT // 2 + idx * CARD_SPACING)

        #sprawdzanie wygranej
        prev_game_won = game_won
        game_won = is_game_won(game_board)

        if game_won and not prev_game_won and final_time is None:
            final_time = (pygame.time.get_ticks() - start_ticks) // 1000
        if game_won:
            #wyswietlanie ekranu wygranej
            win_font = pygame.font.SysFont(None, 80)
            timer_font = pygame.font.SysFont(None, 48)
            win_text = win_font.render('You Win!', True, (255, 215, 0))
            if final_time is not None:
                minutes = final_time // 60
                seconds = final_time % 60
                timer_text = timer_font.render(f"Time: {minutes:02}:{seconds:02}", True, (255, 255, 255))
            else:
                timer_text = timer_font.render("Time: 00:00", True, (255, 255, 255))

            spacing = 20
            total_height = win_text.get_height() + spacing + timer_text.get_height()
            box_width = max(win_text.get_width(), timer_text.get_width()) + 40
            box_height = total_height + 40
            box_rect = pygame.Rect(0, 0, box_width, box_height)
            box_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            pygame.draw.rect(screen, (0, 0, 0), box_rect)

            win_text_rect = win_text.get_rect(center=(box_rect.centerx, box_rect.top + 20 + win_text.get_height() // 2))
            screen.blit(win_text, win_text_rect)

            timer_text_rect = timer_text.get_rect(center=(box_rect.centerx, win_text_rect.bottom + spacing + timer_text.get_height() // 2))
            screen.blit(timer_text, timer_text_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 