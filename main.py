import tkinter as tk
from tkinter import font, Toplevel, Label, Button, PhotoImage, Frame, OptionMenu, StringVar, IntVar, Checkbutton
from tkinter.font import Font
from PIL import Image, ImageTk
import webbrowser
import tkintermapview
from random import randint
from functools import partial
import itertools

# ================== КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ ==================

class Config:
    """
    Класс-контейнер для всех настроек приложения.
    Содержит цвета, шрифты и пути к ресурсам.
    """
    # Основная цветовая гамма
    PURPLE = '#951b81'          # фирменный фиолетовый
    WHITE = 'white'              # белый
    BLACK = 'black'              # чёрный
    GREY = '#7f7679'             # серый для текста
    LIGHT_GREY = 'grey56'        # светло-серый для второстепенных надписей
    BG_DARK = '#24262C'          # тёмный фон (например, в окне выбора мест)
    BG_LIGHT = '#f3f9fd'         # светлый фон
    RED = '#fb3100'              # красный для кнопок навигации
    BUTTON_BG = '#f0f4f7'        # фон кнопок при наведении

    # Шрифты
    FONT_MAIN = ('Helvetica', 12)               # основной текст
    FONT_TITLE = ('Helvetica', 32)               # заголовки окон
    FONT_SUBTITLE = ('Helvetica', 16)             # подзаголовки
    FONT_BUTTON = ('Rostov', 30, 'bold')          # шрифт кнопок главного меню
    FONT_BUTTON_SMALL = ('Calibri', 20)           # шрифт для кнопок помельче

    # Путь к иконке приложения
    ICON_PATH = 'images/icon.ico'  # ИЗМЕНЕНО: добавлен путь images/


# ================== БАЗОВЫЙ КЛАСС ДЛЯ ВСЕХ ОКОН ==================

class BaseWindow:
    """
    Абстрактный базовый класс для всех окон приложения.
    Реализует шаблонный метод: инициализация окна, установка иконки,
    вызов setup_ui() в наследниках и захват фокуса.
    """
    def __init__(self, parent, title='', geometry='1280x960', resizable=(False, False)):
        """
        Конструктор базового окна.
        :param parent: родительское окно (Tk или Toplevel)
        :param title: заголовок окна
        :param geometry: размеры окна (строка вида 'ширинаxвысота')
        :param resizable: кортеж (можно ли менять ширину, можно ли менять высоту)
        """
        self.parent = parent
        self.window = Toplevel(parent)
        self.window.title(title)
        self.window.geometry(geometry)
        self.window.resizable(*resizable)
        # Пытаемся установить иконку, если файл существует
        try:
            self.window.iconbitmap(Config.ICON_PATH)
        except:
            pass
        # Вызов метода создания интерфейса, который должен быть переопределён
        self.setup_ui()
        # Захватываем фокус, чтобы новое окно было активным
        self.window.grab_set()

    def setup_ui(self):
        """
        Метод для создания пользовательского интерфейса.
        Переопределён в дочерних классах.
        """
        raise NotImplementedError


# ================== ФАБРИКА ДЛЯ СОЗДАНИЯ КНОПОК ==================

class ButtonFactory:
    """
    Фабрика, централизованно создающая кнопки с предопределёнными стилями
    и эффектами наведения/смещения.
    """
    @staticmethod
    def create_text_button(parent, text, command, x, y, font=Config.FONT_BUTTON_SMALL,
                           bg=Config.WHITE, fg=Config.PURPLE, active_bg=Config.WHITE, border=0):
        """
        Создаёт текстовую кнопку без эффекта наведения (или с простым).
        :param parent: родительский виджет
        :param text: текст на кнопке
        :param command: функция, вызываемая при нажатии
        :param x, y: координаты размещения
        :param font: шрифт
        :param bg: цвет фона
        :param fg: цвет текста
        :param active_bg: цвет фона при нажатии
        :param border: ширина рамки
        :return: объект Button
        """
        btn = Button(parent, text=text, font=font, bg=bg, fg=fg,
                     activebackground=active_bg, borderwidth=border, command=command)
        btn.place(x=x, y=y)
        return btn

    @staticmethod
    def create_image_button(parent, img_normal, img_hover, command, x, y, bg=Config.WHITE):
        """
        Создаёт кнопку с изображением, которое меняется при наведении мыши.
        :param parent: родительский виджет
        :param img_normal: PhotoImage для обычного состояния
        :param img_hover: PhotoImage для состояния наведения
        :param command: функция при нажатии
        :param x, y: координаты
        :param bg: цвет фона
        :return: объект Button
        """
        btn = Button(parent, image=img_normal, bg=bg, borderwidth=0,
                     activebackground=bg, command=command)

        def on_enter(e):
            btn.config(image=img_hover)

        def on_leave(e):
            btn.config(image=img_normal)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.place(x=x, y=y)
        return btn

    @staticmethod
    def create_nav_button(parent, image, command, x, y, bg, hover_offset=2):
        """
        Создаёт кнопку навигации (влево/вправо), которая немного смещается при наведении.
        :param parent: родительский виджет
        :param image: PhotoImage кнопки
        :param command: функция при нажатии
        :param x, y: исходные координаты
        :param bg: цвет фона
        :param hover_offset: смещение при наведении (пикселей)
        :return: объект Button
        """
        btn = Button(parent, image=image, bg=bg, borderwidth=0, activebackground=bg, command=command)

        def on_enter(e):
            btn.place(x=x + hover_offset, y=y + hover_offset)

        def on_leave(e):
            btn.place(x=x, y=y)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.place(x=x, y=y)
        return btn


# ================== МОДЕЛЬ ДАННЫХ ==================

class MovieData:
    """
    Хранит всю информацию о фильмах и расписании сеансов.
    Используется как источник данных для всех окон.
    """
    # Словарь с детальным описанием каждого фильма.
    # Ключ — название фильма (строго соответствует именам в расписании и постерам).
    movie_details = {
        'Майор Гром: Игра': {
            'duration': '3 часа',
            'genre': 'Приключения, экшн 16+',
            'country': 'Россия',
            'director': 'Олег Трофим',
            'actors': 'Тихон Жизневский, Александр Сетейкин, Алексей Маклаков, Любовь Аксенова, Сергей Горошко, Константин Хабенский, Матвей Лыков, Ольга Сутулова',
            'description': 'Сюжет «Игры» разворачивается спустя год после того, как майор Гром поймал Чумного Доктора. Санкт-Петербург оправился от потрясений, Сергей Разумовский оказался в психиатрической лечебнице, а Игорь Гром стал главной знаменитостью в городе. Жизнь майора Грома идеальна: днем он ловит преступников вместе с напарником Димой Дубиным, а вечера проводит в компании журналистки Юлии Пчёлкиной. Полную идиллию прерывает появление в городе таинственного злодея, называющего себя Призраком. Он предлагает Грому сыграть в опасную игру, ставка в которой — жизни обычных людей.'
        },
        'Министерство неджентельменских дел': {
            'duration': '2 часа 7 минут',
            'genre': 'Комедийный экшн 18+',
            'country': 'США, Великобритания',
            'director': 'Гай Ричи',
            'actors': 'Генри Кавилл, Эйса Гонсалес, Алан Ричсон, Алекс Петтифер',
            'description': 'Они — лучшие из лучших. Отпетые авантюристы и первоклассные спецы, привыкшие действовать в одиночку. Но когда на кону стоит судьба всего мира, им приходится объединиться в сверхсекретное боевое подразделение и отправиться на дерзкую миссию против нацистов. Теперь их дело — война, и вести они её будут совершенно не по-джентльменски.'
        },
        'Планета обезьян: Новое царство': {
            'duration': '2 часа 30 минут',
            'genre': 'Фантастика, боевик, приключения 16+',
            'country': 'США',
            'director': 'Уэс Болл',
            'actors': 'Оуэн Тиг, Питер Макон, Фрейя Аллан',
            'description': 'Несколько поколений после правления Цезаря. Обезьяны являются доминирующим видом, живущим в гармонии, а люди вынуждены оставаться в тени. Пока новый тиранический лидер обезьян строит свою империю, один молодой шимпанзе отправляется в путешествие, которое заставит его усомниться во всём, что он знал о прошлом, и сделать выбор, который определит будущее как обезьян, так и людей.'
        },
        'Пушистый вояж': {
            'duration': '1 час 33 минуты',
            'genre': 'Мультфильм, комедия, приключения 6+',
            'country': 'США, Канада',
            'director': 'Кевин Донован, Готтфрид Рудт',
            'actors': 'Билл Найи, Брук Шилдс, Дэнни Трехо',
            'description': 'Во время переезда двое домашних любимцев, Педро и Грейси, теряют своих хозяев. Оказавшись в пугающем и неизвестном мире, они пытаются воссоединиться с семьей. На пути их ждет множество приключений и опасностей, справиться с которыми можно, только действуя сообща. Смогут ли они разрешить свои разногласия и вернуться домой?'
        },
        'Сто лет тому вперед': {
            'duration': '2 часа 35 минут',
            'genre': 'Приключения, экшн 6+',
            'country': 'Россия',
            'director': 'Александр Андрющенко',
            'actors': 'Даша Верещагина, Марк Эйдельштейн, Александр Петров, Юра Борисов, Виктория Исакова, Константин Хабенский, Федор Бондарчук, Софа Цибирева',
            'description': 'Они живут в разных мирах. Коля Герасимов — в сегодняшней Москве, Алиса Селезнева — на сто лет позже. Коля – обычный парень, ему нет дела до будущего. Алису не отпускает прошлое: она должна найти маму, которую потеряла, когда была совсем ребенком. Встреча Алисы и Коли станет началом невероятных приключений, в которых нашим героям предстоит отвоевать у космических пиратов Вселенную, восстановить ход времени и обрести самое дорогое: любовь и дружбу.'
        },
        'Незнакомцы': {
            'duration': '1 час 37 минут',
            'genre': 'Хоррор-слэшер 18+',
            'country': 'США',
            'director': 'Ренни Харлин',
            'actors': 'Мэделин Петш, Гэбриел Бассо, Рэйчел Шентон, Ричард Брэйк',
            'description': 'Майя и Райан решили отметить пятую годовщину, не подозревая, что она может стать их последней. Путешествуя на своем пикапе через всю страну, они совершают вынужденную остановку в маленьком городе, где местные жители, даже дети, встречают их с большим интересом. Оставаться в этом странном месте пара не хочет, но вынуждена провести ночь в доме, куда вскоре нагрянут безумцы в кукольных масках.'
        },
        'Винни Пух: Кровь и мёд': {
            'duration': '1 час 37 минут',
            'genre': 'Ужасы, триллер 18+',
            'country': 'Великобритания',
            'director': 'Рис Фрейк-Уотерфилд',
            'actors': 'Скотт Чемберс, Таллула Эванс, Райан Олива, Тереза Бенхем',
            'description': 'После событий первого фильма, Винни-Пух и Пятак больше не могут продолжать охотиться в Стоакровом лесу. Очередное предательство Кристофера Робина, раскрывшего миру их существование, ставит под угрозу не только их дом, но и жизни. Вот только звери больше не намерены прятаться в тени и вместе с друзьями Совенком и Тигрой отправляются в город, чтобы навести в нем свои кровавые порядки.'
        },
        'Суперпташки': {
            'duration': '1 час 31 минута',
            'genre': 'Анимация 0+',
            'country': 'Италия, Испания',
            'director': 'Нестор Ф. Деннис',
            'actors': 'Тай Шеридан, Шон Пенн, Гбенга Акиннагбе',
            'description': 'Птичка Джонни и его пернатые друзья обладают суперспособностями. Однажды они отправляются на секретную миссию, в ходе которой им предстоит спасти родной город от коварных планов злодея Отто фон Моржа.'
        },
        'Судная ночь': {
            'duration': '1 час 34 минуты',
            'genre': 'Криминал, триллер 18+',
            'country': 'США',
            'director': 'Дэн Браун',
            'actors': 'Ангус Клауд, Эллиот Найт, Джессика Гарза',
            'description': 'Несколько человек становятся свидетелями джекпота в $156 миллионов долларов. Случайные посетители, полиция, преступники - все желают заполучить лотерейный билет с огромным выигрышем. Эта судная ночь выпустит на волю все людские пороки.'
        },
        'Асфальтовые джунгли': {
            'duration': '2 часа 5 минут',
            'genre': 'Триллер, драма 18+',
            'country': 'США',
            'director': 'Жан-Стефан Совер',
            'actors': 'Тай Шеридан, Шон Пенн, Гбенга Акиннагбе',
            'description': 'Это история врача и его первого года на работе в середине 90-х в Гарлеме. Это взгляд изнутри на уличную жизнь: перестрелки, плохие копы, безнадежные пациенты, черный юмор в странных обстоятельствах и попытка одного медика сохранить свое желание помочь, несмотря на его растущую черствость.'
        }
    }

    # Расписание сеансов. Ключ — дата (строка), значение — список кортежей:
    # (название фильма, название кинотеатра, список времени сеансов)
    schedule = {
        '29.05.2024': [
            ('Майор Гром: Игра', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Майор Гром: Игра', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Майор Гром: Игра', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Министерство неджентельменских дел', 'Премьер Зал Парк Хаус', ['10:00', '13:15']),
            ('Министерство неджентельменских дел', 'ККЦ "Премьер Зал Омега"', ['12:40', '15:15', '19:50']),
            ('Министерство неджентельменских дел', 'ККЦ "Премьер Зал Гранат"', ['10:10', '13:15', '21:40']),
            ('Планета обезьян: Новое царство', 'Премьер Зал Парк Хаус', ['16:20', '18:30', '21:40']),
            ('Планета обезьян: Новое царство', 'ККЦ "Премьер Зал Омега"', ['21:40', '23:00', '00:20']),
            ('Планета обезьян: Новое царство', 'ККЦ "Премьер Зал Гранат"', ['17:45', '23:10']),
            ('Пушистый вояж', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Пушистый вояж', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Пушистый вояж', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Сто лет тому вперед', 'Премьер Зал Парк Хаус', ['11:20', '16:10']),
            ('Сто лет тому вперед', 'ККЦ "Премьер Зал Омега"', ['10:20', '14:30', '19:50']),
            ('Сто лет тому вперед', 'ККЦ "Премьер Зал Гранат"', ['11:50', '17:40', '23:20']),
            ('Незнакомцы', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Незнакомцы', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Незнакомцы', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Винни Пух: Кровь и мёд', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Винни Пух: Кровь и мёд', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Винни Пух: Кровь и мёд', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Суперпташки', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Суперпташки', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Суперпташки', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Судная ночь', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Судная ночь', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Судная ночь', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
            ('Асфальтовые джунгли', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Асфальтовые джунгли', 'ККЦ "Премьер Зал Омега"', ['10:30', '17:45']),
            ('Асфальтовые джунгли', 'ККЦ "Премьер Зал Гранат"', ['11:45', '14:50', '19:50']),
        ],
        '30.05.2024': [
            ('Незнакомцы', 'Премьер Зал Парк Хаус', ['11:45', '14:50', '19:50']),
            ('Винни Пух: Кровь и мёд', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Суперпташки', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Судная ночь', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Асфальтовые джунгли', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
        ],
        '31.05.2024': [
            ('Министерство неджентельменских дел', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Пушистый вояж', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Незнакомцы', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Суперпташки', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Асфальтовые джунгли', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
        ],
        '01.06.2024': [
            ('Майор Гром: Игра', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Планета обезьян: Новое царство', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Сто лет тому вперед', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Винни Пух: Кровь и мёд', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Судная ночь', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
        ],
        '02.06.2024': [
            ('Планета обезьян: Новое царство', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Пушистый вояж', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Сто лет тому вперед', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Незнакомцы', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
            ('Винни Пух: Кровь и мёд', 'Премьер Зал Парк Хаус', ['11:45', '14:50']),
        ]
    }


# ================== ГЛАВНОЕ ОКНО ==================

class MainWindow:
    """
    Главное окно приложения. Содержит карусель изображений,
    информационные тексты и кнопки перехода к другим разделам.
    """
    def __init__(self):
        # Создаём корневое окно Tk
        self.root = tk.Tk()
        self.root.geometry('1280x960')
        self.root.title('ПРЕМЬЕР ЗАЛ')
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(Config.ICON_PATH)
        except:
            pass

        # Загружаем все необходимые изображения
        self.images = self._load_images()
        # Индекс текущего изображения в карусели
        self.current_img_index = 0
        # Список изображений для карусели
        self.main_images = [self.images['main1'], self.images['main2'], self.images['main3']]

        # Строим интерфейс
        self._setup_ui()
        # Запускаем автоматическую смену изображений
        self._start_slideshow()

    def _load_images(self):
        """
        Загружает изображения для главного окна.
        Возвращает словарь с загруженными PhotoImage.
        """
        imgs = {}
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            imgs['main1'] = PhotoImage(file='images/main1.png')
            imgs['main2'] = PhotoImage(file='images/main2.png')
            imgs['main3'] = PhotoImage(file='images/main3.png')
            imgs['r'] = ImageTk.PhotoImage(Image.open('images/r.png').resize((45, 60)))   # ИЗМЕНЕНО
            imgs['l'] = ImageTk.PhotoImage(Image.open('images/l.png').resize((45, 60)))   # ИЗМЕНЕНО
        except Exception as e:
            print(f'Ошибка загрузки изображений: {e}')
        return imgs

    def _setup_ui(self):
        """Размещает все элементы интерфейса главного окна."""
        # Фоновая метка с первым изображением
        self.bg_label = Label(self.root, image=self.main_images[0])
        self.bg_label.place(x=-2, y=0)

        # Три информационных блока (текст взят из оригинального приложения)
        text1 = ('Компания «Премьер Зал» появилась в 1998 году, именно тогда мы открыли свой первый кинотеатр. '
                 'Мы развивали наш бренд, и уже сейчас в нашей Сети 4 кинотеатра в Екатеринбурге и свыше 300 – '
                 'по всей стране! Наши площадки оснащены современным и технологичным оборудованием '
                 '– это звуковая система Dolby, комфортные кресла-реклайнеры c регуляцией положения '
                 'и встроенной зарядкой, многофункциональный консешн-бар и изготовление попкорна по '
                 'специальной технологии.')
        Label(self.root, text=text1, font=Config.FONT_MAIN, bg=Config.WHITE,
              fg=Config.GREY, width=45, justify='left').place(x=60, y=730)

        text2 = ('В наших кинотеатрах можно не просто посмотреть кино в хорошем качестве, но и перекусить '
                 'классным попкорном и разными снеками, интересно и познавательно провести время с '
                 'друзьями и семьей. Кинотеатры «Премьер Зала» доступны для зрителей и по ценам, и по '
                 'расположению, поэтому до нас вы легко доберетесь и после работы, и в выходной день! '
                 'На наших площадках мы также проводим различные культурные мероприятия: устраиваем праздники, '
                 'концерты и лекции, проводим фестивали')
        Label(self.root, text=text2, font=Config.FONT_MAIN, bg=Config.WHITE,
              fg=Config.GREY, width=46, justify='left').place(x=440, y=730)

        text3 = ('мастер-классы, клубы по интересам. Наши кинотеатры становятся полноценными '
                 'культурными центрами, где найдется место для любого досуга – детского, семейного, '
                 'развлекательного и интеллектуального. У нас вы отлично проведете время и с ребенком, '
                 'и с коллегами, и на романтическом свидании. Задача «Премьер Зала» – обеспечить наших '
                 'гостей качественным и интересным досугом, создать комфортные условия.')
        Label(self.root, text=text3, font=Config.FONT_MAIN, bg=Config.WHITE,
              fg=Config.GREY, width=42, justify='left').place(x=830, y=730)

        # Кнопки навигации по страницам (Фильмы, Расписание, Контакты)
        btn_font = Font(family="Rostov", size=30, weight="bold")

        def create_nav_btn(text, x, cmd):
            """Внутренняя функция для создания кнопки с эффектом смены цвета текста."""
            btn = Button(self.root, bg=Config.WHITE, borderwidth=0, text=text, fg=Config.BLACK,
                         font=btn_font, activebackground=Config.WHITE, activeforeground=Config.BLACK,
                         command=cmd)
            btn.place(x=x, y=23)

            def on_enter(e):
                btn.config(fg=Config.PURPLE)

            def on_leave(e):
                btn.config(fg=Config.BLACK)

            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

        create_nav_btn('ФИЛЬМЫ', 300, lambda: PosterWindow(self.root))
        create_nav_btn('РАСПИСАНИЕ', 550, lambda: ScheduleWindow(self.root))
        create_nav_btn('КОНТАКТЫ', 865, lambda: ContactsWindow(self.root))

        # Кнопки переключения карусели (влево/вправо)
        ButtonFactory.create_nav_button(
            self.root, self.images['r'], self._next_image, 1230, 380, Config.RED
        )
        ButtonFactory.create_nav_button(
            self.root, self.images['l'], self._prev_image, 8, 380, Config.RED
        )

    def _next_image(self):
        """Переключает на следующее изображение в карусели."""
        self.current_img_index = (self.current_img_index + 1) % len(self.main_images)
        self.bg_label.config(image=self.main_images[self.current_img_index])

    def _prev_image(self):
        """Переключает на предыдущее изображение в карусели."""
        self.current_img_index = (self.current_img_index - 1) % len(self.main_images)
        self.bg_label.config(image=self.main_images[self.current_img_index])

    def _start_slideshow(self):
        """Запускает автоматическую смену изображений каждые 5 секунд."""
        def update():
            self._next_image()
            self.root.after(5000, update)

        self.root.after(5000, update)

    def run(self):
        """Запускает главный цикл обработки событий."""
        self.root.mainloop()


# ================== ОКНО АФИШИ ==================

class PosterWindow(BaseWindow):
    """
    Окно с постерами фильмов. При клике на постер открывается окно с детальным описанием.
    """
    def setup_ui(self):
        # Устанавливаем фоновое изображение, если есть
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            bg_img = PhotoImage(file='images/фон афиша.png')
            Label(self.window, image=bg_img).pack(anchor=tk.W)
            self.bg_img = bg_img  # сохраняем ссылку, чтобы изображение не удалилось
        except:
            pass

        # Заголовок
        Label(self.window, text='Выберите фильм', font=Config.FONT_TITLE).place(x=264, y=120)

        # Список постеров: (обычное изображение, изображение при наведении, название фильма)
        posters = [
            ('Майор Гром.png', 'Майор Гром темный.png', 'Майор Гром: Игра'),
            ('Министерство неджентельменских дел.png', 'Министерство неджентельменских дел темный.png', 'Министерство неджентельменских дел'),
            ('Планета обезьян.png', 'Планета обезьян темный.png', 'Планета обезьян: Новое царство'),
            ('Пушистый вояж.png', 'Пушистый вояж темный.png', 'Пушистый вояж'),
            ('Сто лет тому вперед.png', 'Сто лет тому вперед темный.png', 'Сто лет тому вперед'),
            ('незнакомцы.png', 'Незнакомцы темная.png', 'Незнакомцы'),
            ('Винни Пух.png', 'Винни Пух темный.png', 'Винни Пух: Кровь и мёд'),
            ('суперпташки.png', 'суперпташки темная.png', 'Суперпташки'),
            ('судная ночь.png', 'судная ночь темный.png', 'Судная ночь'),
            ('Асфальтовые джунгли.png', 'Асфальтовые джунгли темный.png', 'Асфальтовые джунгли'),
        ]

        # Координаты для двух рядов по 5 постеров (верхний ряд и нижний)
        positions = [
            (264, 200), (417, 200), (567, 200), (716, 200), (864, 200),
            (264, 519), (417, 519), (567, 519), (716, 519), (864, 519)
        ]

        self.poster_images = {}  # храним ссылки на все загруженные изображения

        for i, (norm, hover, title) in enumerate(posters):
            try:
                # ИЗМЕНЕНО: добавлен путь images/ к каждому файлу
                img_norm = PhotoImage(file='images/' + norm)
                img_hover = PhotoImage(file='images/' + hover)
                self.poster_images[norm] = img_norm
                self.poster_images[hover] = img_hover

                # Создаём кнопку с эффектом наведения через фабрику
                ButtonFactory.create_image_button(
                    self.window, img_norm, img_hover,
                    lambda t=title: self._show_movie_details(t),  # при нажатии передаём название фильма
                    positions[i][0], positions[i][1], bg=Config.WHITE
                )
            except Exception as e:
                print(f'Не удалось загрузить {norm}: {e}')

    def _show_movie_details(self, title):
        """
        Открывает новое окно с подробной информацией о выбранном фильме.
        :param title: название фильма
        """
        data = MovieData.movie_details.get(title, {})
        if not data:
            return

        # Создаём дочернее окно
        w = Toplevel(self.window)
        w.title(f'О ФИЛЬМЕ {title.upper()}')
        w.iconbitmap(Config.ICON_PATH)
        w.geometry('1280x960')
        w.resizable(False, False)

        # Фон
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            bg = PhotoImage(file='images/фон афиша.png')
            Label(w, image=bg).pack(anchor=tk.W)
            w.bg = bg
        except:
            pass

        # Заголовок
        Label(w, text=f'О ФИЛЬМЕ {title.upper()}', font=Config.FONT_TITLE).place(x=264, y=120)

        # Длительность и жанр
        Label(w, text=f"{data['duration']} {data['genre']}", font=Config.FONT_SUBTITLE).place(x=220, y=240)
        # Страна
        Label(w, text=f"Страна: {data['country']}", font=Config.FONT_SUBTITLE).place(x=220, y=290)
        # Режиссёр
        Label(w, text=f"Режиссер: {data['director']}", font=Config.FONT_SUBTITLE).place(x=220, y=340)
        # Актёры (может быть длинная строка)
        Label(w, text=f"Актеры: {data['actors']}", font=Config.FONT_SUBTITLE, justify='left').place(x=220, y=390)
        # Описание (разбиваем на строки по исходному тексту, если есть переносы)
        desc_lines = data['description'].split('\n')
        y_desc = 440
        for line in desc_lines:
            Label(w, text=line, font=Config.FONT_SUBTITLE, justify='left').place(x=220, y=y_desc)
            y_desc += 40

        w.grab_set()
        w.mainloop()


# ================== ОКНО ВЫБОРА МЕСТ ==================

class SeatSelectionWindow(BaseWindow):
    """
    Окно для выбора мест в кинозале.
    Отображает схему зала, позволяет выбирать места, запоминает выбранные.
    """
    def __init__(self, parent, movie_title, session_time, cinema_name):
        """
        :param parent: родительское окно
        :param movie_title: название фильма
        :param session_time: время сеанса
        :param cinema_name: название кинотеатра
        """
        self.movie_title = movie_title
        self.session_time = session_time
        self.cinema_name = cinema_name
        self.selected_seats = []          # список выбранных мест (строки вида "Ряд X место Y")
        self.seat_buttons = {}             # словарь для хранения кнопок мест (ключ — строка с местом)
        super().__init__(parent, 'Выбор места', '1024x720')

    def setup_ui(self):
        self.window.configure(bg=Config.BG_DARK)
        self._load_images()
        self._create_header()
        self._create_screen()
        self._create_seats()
        self._create_buy_button()

    def _load_images(self):
        """Загружает изображения для кнопок мест и кнопки покупки."""
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            self.seat_normal = PhotoImage(file='images/seet.png')
            self.seat_pressed = PhotoImage(file='images/seet_press.png')
            self.buy_image = PhotoImage(file='images/buy.png')
        except:
            pass

    def _create_header(self):
        """Создаёт верхнюю часть окна с названием фильма, временем и разделительной линией."""
        Label(self.window, text=self.movie_title, font=Config.FONT_BUTTON_SMALL,
              bg=Config.BG_DARK, fg=Config.WHITE).place(x=10, y=10)
        Label(self.window, text=self.session_time, font=('Calibri', 15),
              bg=Config.BG_DARK, fg=Config.LIGHT_GREY).place(x=10, y=45)
        # Белая линия-разделитель
        Frame(self.window, bg=Config.WHITE, height=1, width=1280).place(x=0, y=90)

    def _create_screen(self):
        """Рисует надпись 'ЭКРАН' в верхней части зала."""
        Label(self.window, text='ЭКРАН', font='Calibri 23',
              bg=Config.BG_DARK, fg=Config.LIGHT_GREY).place(x=450, y=110)

    def _create_seats(self):
        """
        Создаёт места согласно конфигурации зала.
        Конфигурация повторяет оригинальную: 5 рядов, в первых четырёх по 5 мест слева и 5 справа,
        в пятом ряду слева 8 мест, справа 5 мест.
        """
        # Конфигурация рядов: для каждого ряда задаём Y-координату и списки X-координат для левой и правой групп
        rows_config = [
            {'y': 200, 'left': [170, 220, 270, 320, 370], 'right': [570, 620, 670, 720, 770]},
            {'y': 300, 'left': [170, 220, 270, 320, 370], 'right': [570, 620, 670, 720, 770]},
            {'y': 400, 'left': [170, 220, 270, 320, 370], 'right': [570, 620, 670, 720, 770]},
            {'y': 500, 'left': [170, 220, 270, 320, 370], 'right': [570, 620, 670, 720, 770]},
            {'y': 600, 'left': [170, 220, 270, 320, 370, 420, 470, 520], 'right': [570, 620, 670, 720, 770]},
        ]

        for row_idx, row in enumerate(rows_config, start=1):
            # Левая группа мест
            for col_idx, x in enumerate(row['left'], start=1):
                self._create_seat_button(row_idx, col_idx, x, row['y'])
            # Правая группа мест (нумерация колонок продолжается)
            for col_idx, x in enumerate(row['right'], start=len(row['left']) + 1):
                self._create_seat_button(row_idx, col_idx, x, row['y'])

    def _create_seat_button(self, row, col, x, y):
        """
        Создаёт одну кнопку места, привязывает обработчик клика.
        :param row: номер ряда
        :param col: номер места
        :param x: координата X
        :param y: координата Y
        """
        seat_id = f'Ряд {row} место {col}'
        btn = Button(self.window, image=self.seat_normal, borderwidth=0,
                     bg=Config.BG_DARK, activebackground=Config.BG_DARK)

        def on_click(e):
            # Если место свободно (NORMAL) — выбираем его
            if btn.cget('state') == tk.NORMAL:
                btn.config(image=self.seat_pressed, state=tk.DISABLED)
                self.selected_seats.append(seat_id)
            else:
                # Если уже выбрано — отменяем выбор
                btn.config(image=self.seat_normal, state=tk.NORMAL)
                self.selected_seats.remove(seat_id)

        btn.bind('<Button-1>', on_click)
        btn.place(x=x, y=y)
        self.seat_buttons[seat_id] = btn

    def _create_buy_button(self):
        """Создаёт кнопку 'Купить', которая открывает окно билета."""
        def buy():
            if not self.selected_seats:
                # Можно добавить всплывающее предупреждение, но в оригинале его не было
                return
            TicketWindow(self.window, self.movie_title, self.session_time,
                         self.cinema_name, self.selected_seats)

        ButtonFactory.create_image_button(
            self.window, self.buy_image, self.buy_image, buy, 830, -5, bg=Config.BG_DARK
        )


# ================== ОКНО БИЛЕТА ==================

class TicketWindow(BaseWindow):
    """
    Окно с электронным билетом после успешной покупки.
    Содержит номер заказа, информацию о фильме, выбранные места и стоимость.
    """
    def __init__(self, parent, movie_title, session_time, cinema_name, selected_seats):
        """
        :param parent: родительское окно
        :param movie_title: название фильма
        :param session_time: время сеанса
        :param cinema_name: кинотеатр
        :param selected_seats: список выбранных мест
        """
        self.movie_title = movie_title
        self.session_time = session_time
        self.cinema_name = cinema_name
        self.selected_seats = selected_seats
        # Генерируем случайный номер заказа из 9 цифр
        self.order_number = randint(100_000_000, 999_999_999)
        super().__init__(parent, 'ЭЛЕКТРОННЫЙ БИЛЕТ', '600x400')

    def setup_ui(self):
        self.window.configure(bg=Config.WHITE)
        self._load_images()
        self._create_content()

    def _load_images(self):
        """Загружает фоновое изображение и иконку для билета."""
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            self.bg = ImageTk.PhotoImage(Image.open('images/фон1_белый.png').resize((600, 400)))
            self.icon = ImageTk.PhotoImage(Image.open('images/icon.png').resize((150, 150)))   # ИЗМЕНЕНО
        except:
            pass
        Label(self.window, image=self.bg).place(x=-2, y=0)

    def _create_content(self):
        """Размещает всю информацию на билете."""
        Label(self.window, text='Вы успешно купили билет',
              font=('Helvetica', 20), bg=Config.WHITE).place(x=130, y=30)

        Label(self.window, text='Номер заказа', font=('Helvetica', 16), bg=Config.WHITE).place(x=50, y=80)
        # Форматируем номер заказа: три группы по три цифры
        order_str = f'{str(self.order_number)[0:3]} {str(self.order_number)[3:6]} {str(self.order_number)[6:]}'
        Label(self.window, text=order_str, font=('Helvetica', 22, 'bold'), bg=Config.WHITE).place(x=50, y=110)

        Label(self.window, text=f'Фильм: {self.movie_title}', font=('Helvetica', 12), bg=Config.WHITE).place(x=50, y=160)
        Label(self.window, text=f'Кинотеатр: {self.cinema_name}', font=('Helvetica', 12), bg=Config.WHITE).place(x=50, y=185)
        Label(self.window, text=f'Сеанс: {self.session_time}', font=('Helvetica', 12), bg=Config.WHITE).place(x=50, y=210)

        total = len(self.selected_seats) * 230
        Label(self.window, text=f'Стоимость билетов: {total}', font=('Helvetica', 12), bg=Config.WHITE).place(x=50, y=235)

        Label(self.window, text='Мест:', font=('Helvetica', 12), bg=Config.WHITE).place(x=50, y=260)
        # Выводим список мест, каждое с новой строки
        seats_text = '\n'.join(self.selected_seats)
        Label(self.window, text=seats_text, height=5, width=30, bg='cyan',
              font=('Helvetica', 12), anchor='nw').place(x=100, y=260)

        # Иконка в правом нижнем углу
        Label(self.window, image=self.icon, bg=Config.WHITE).place(x=400, y=100)


# ================== ОКНО РАСПИСАНИЯ ==================

class ScheduleWindow(BaseWindow):
    """
    Окно с расписанием сеансов.
    Содержит прокручиваемую область, выбор даты и кнопки для каждого сеанса.
    """
    def setup_ui(self):
        self.window.geometry('1280x960')
        self._load_images()
        self._create_scroll_area()
        self._fill_schedule()

    def _load_images(self):
        """Загружает изображения постеров для использования в расписании."""
        self.poster_images = {}
        poster_files = [
            'Майор Гром.png', 'Министерство неджентельменских дел.png', 'Планета обезьян.png',
            'Пушистый вояж.png', 'Сто лет тому вперед.png', 'незнакомцы.png', 'Винни Пух.png',
            'суперпташки.png', 'судная ночь.png', 'Асфальтовые джунгли.png'
        ]
        for f in poster_files:
            try:
                # ИЗМЕНЕНО: добавлен путь images/
                self.poster_images[f] = ImageTk.PhotoImage(file='images/' + f)
            except:
                pass

    def _create_scroll_area(self):
        """Создаёт холст с полосой прокрутки для длинного расписания."""
        self.scroll_frame = tk.Frame(self.window)
        self.scroll_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.scroll_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.scroll_frame, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.config(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.config(scrollregion=self.canvas.bbox('all')))

        # Привязка колеса мыши к прокрутке
        def on_mousewheel(event):
            self.canvas.yview_scroll(-1 * (event.delta // 120), 'units')
        self.canvas.bind_all('<MouseWheel>', on_mousewheel)

        # Фоновое изображение (если есть)
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            bg = tk.PhotoImage(file='images/raspback2.png')
            self.canvas.create_image(0, 0, image=bg, anchor=tk.NW)
            self.canvas.image = bg
        except:
            pass

        self.canvas.create_text(400, 200, text='Расписание', fill='Black', font=('Rostov', 48))

        # Выпадающий список для выбора даты
        self.selected_date = StringVar(self.canvas)
        self.selected_date.set('29.05.2024')
        dates = ['29.05.2024', '30.05.2024', '31.05.2024', '1.06.2024', '2.06.2024']
        custom_font = Font(family='Helvetica', size=14)
        dropdown = OptionMenu(self.canvas, self.selected_date, *dates)
        dropdown_window = self.canvas.create_window(230, 270, anchor=tk.NW, window=dropdown)
        dropdown.config(font=custom_font)
        # При изменении даты перестраиваем расписание
        self.selected_date.trace('w', lambda *args: self._refresh_schedule())

    def _refresh_schedule(self):
        """
        Очищает холст и заново отображает расписание для выбранной даты.
        """
        # Удаляем всё с холста
        self.canvas.delete('all')

        # Восстанавливаем фон и заголовок
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            bg = tk.PhotoImage(file='images/raspback2.png')
            self.canvas.create_image(0, 0, image=bg, anchor=tk.NW)
            self.canvas.image = bg
        except:
            pass
        self.canvas.create_text(400, 200, text='Расписание', fill='Black', font=('Rostov', 48))

        # Восстанавливаем выпадающий список
        dates = ['29.05.2024', '30.05.2024', '31.05.2024', '1.06.2024', '2.06.2024']
        custom_font = Font(family='Helvetica', size=14)
        dropdown = OptionMenu(self.canvas, self.selected_date, *dates)
        dropdown_window = self.canvas.create_window(230, 270, anchor=tk.NW, window=dropdown)
        dropdown.config(font=custom_font)

        # Получаем данные для выбранной даты
        date = self.selected_date.get()
        schedule_for_date = MovieData.schedule.get(date, [])

        # Переменная для вертикального смещения при отрисовке
        y_offset = 380
        for movie, cinema, times in schedule_for_date:
            # Постер: пытаемся найти соответствующий файл по названию фильма
            poster_key = None
            for k in self.poster_images:
                # Упрощённое сравнение: убираем пробелы и знаки препинания, приводим к нижнему регистру
                if movie.lower().replace(':', '').replace(' ', '') in k.lower().replace('_', '').replace('-', ''):
                    poster_key = k
                    break
            if poster_key:
                self.canvas.create_image(300, y_offset, image=self.poster_images[poster_key])

            # Название кинотеатра
            self.canvas.create_text(420, y_offset + 30, text=cinema, fill='Black',
                                     width=270, font=('Helvetica', 15), anchor=tk.W)

            # Кнопки времени сеансов
            for i, t in enumerate(times):
                # Создаём рамку для кнопки (имитация обводки)
                btn_frame = tk.Frame(self.canvas, highlightbackground=Config.PURPLE,
                                      highlightcolor=Config.PURPLE, highlightthickness=2, bd=0)
                btn = tk.Button(btn_frame, text=t, font=('Helvetica', 12, 'bold'),
                                fg=Config.PURPLE, bd=0, padx=7, pady=3,
                                command=partial(self._open_seat_selection, movie, t, cinema))
                btn.pack()

                # Эффект наведения: меняем цвета кнопки
                def on_enter(e, b=btn):
                    b.config(bg=Config.PURPLE, fg=Config.BLACK)

                def on_leave(e, b=btn):
                    b.config(bg=Config.BUTTON_BG, fg=Config.PURPLE)

                btn.bind('<Enter>', on_enter)
                btn.bind('<Leave>', on_leave)

                # Размещаем рамку с кнопкой на холсте
                self.canvas.create_window(700 + i * 100, y_offset + 15, anchor=tk.NW, window=btn_frame)

            # Увеличиваем отступ для следующего фильма
            y_offset += 150

    def _fill_schedule(self):
        """Первоначальное заполнение расписания (для даты по умолчанию)."""
        self._refresh_schedule()

    def _open_seat_selection(self, movie, time, cinema):
        """Открывает окно выбора мест для выбранного сеанса."""
        SeatSelectionWindow(self.window, movie, time, cinema)


# ================== ОКНО КОНТАКТОВ ==================

class ContactsWindow(BaseWindow):
    """
    Окно с контактной информацией, кнопками соцсетей и картой.
    """
    def setup_ui(self):
        self.window.geometry('1200x700')
        self._load_images()
        self._create_text()
        self._create_social_buttons()
        self._create_map_button()

    def _load_images(self):
        """Загружает иконки для соцсетей и карты (обычные и при наведении)."""
        self.icons = {}
        icons_map = {
            'vk': ('vk.png', 'vk_t.png'),
            'youtube': ('youtube.png', 'youtube_t.png'),
            'twitter': ('twitter.png', 'twitter_t.png'),
            'odnokl': ('odnokl.png', 'odnokl_t.png'),
            'map': ('map.png', 'map_t.png'),
        }
        for name, (norm, hover) in icons_map.items():
            try:
                # ИЗМЕНЕНО: добавлен путь images/
                self.icons[f'{name}_norm'] = ImageTk.PhotoImage(Image.open('images/' + norm).resize((40, 40)))
                self.icons[f'{name}_hover'] = ImageTk.PhotoImage(Image.open('images/' + hover).resize((40, 40)))
            except:
                pass

        # Фоновое изображение
        try:
            # ИЗМЕНЕНО: добавлен путь images/
            bg_img = ImageTk.PhotoImage(Image.open('images/фон афиша.png').resize((1200, 700)))
            Label(self.window, image=bg_img).pack()
            self.bg_img = bg_img
        except:
            pass

    def _create_text(self):
        """Размещает текстовые блоки с контактной информацией."""
        Label(self.window, text='Контактная информация', font=Config.FONT_TITLE).place(x=190, y=80)

        texts = [
            ('Сеть кинотеатров «Премьер Зал» - это уникальный холдинг, в который входит '
             '3 собственных кинотеатра в Екатеринбурге и свыше 300 кинотеатров-партнеров по всей России', 150),
            ('— ККЦ «Омега», г. Екатеринбург, просп. Космонавтов, 41, 4 этаж, тел.: 23-666-65', 210),
            ('— «Премьер Зал Гранат», г. Екатеринбург, ул.Амундсена, 63, 3 этаж, тел.: 23-666-61', 240),
            ('— «Премьер Зал Парк Хаус», г. Екатеринбург, ул.Сулимова, 50, 3 этаж, тел.: 23-666-67', 270),
            ('Единый справочный номер: 3-726-726', 300),
            ('Отдел персонала:', 340),
            ('тел.: 8-932-123-89-37, эл. почта: personal@premierzal.ru', 370),
            ('Мы в соцсетях', 400),
            ('Местоположение', 500)
        ]
        for text, y in texts:
            # Для заголовков разделов используем шрифт побольше и полужирный
            if 'Местоположение' in text or 'Мы в соцсетях' in text:
                font = Config.FONT_SUBTITLE
                weight = 'bold'
            else:
                font = Config.FONT_MAIN
                weight = 'normal'
                # Для строк с номером и отделом персонала делаем полужирным
                if 'номер:' in text or 'персонала:' in text:
                    weight = 'bold'
            Label(self.window, text=text, font=(font[0], font[1], weight), bg=Config.WHITE).place(x=190, y=y)

    def _create_social_buttons(self):
        """Создаёт кнопки для перехода в социальные сети."""
        x = 190
        for name, url in [('vk', 'https://vk.com/premierzal'),
                          ('youtube', 'https://www.youtube.com/channel/UCf2QiK-LXkqsJYNLMdkWD6A'),
                          ('twitter', 'https://x.com/premierzal?mx=2'),
                          ('odnokl', 'https://ok.ru/premierzal')]:
            if f'{name}_norm' in self.icons:
                ButtonFactory.create_image_button(
                    self.window, self.icons[f'{name}_norm'], self.icons[f'{name}_hover'],
                    lambda u=url: webbrowser.open(u), x, 450, bg=Config.WHITE
                )
                x += 60

    def _create_map_button(self):
        """Создаёт кнопку для открытия карты."""
        def open_map():
            MapWindow(self.window)

        if 'map_norm' in self.icons:
            ButtonFactory.create_image_button(
                self.window, self.icons['map_norm'], self.icons['map_hover'],
                open_map, 190, 550, bg=Config.WHITE
            )


# ================== ОКНО КАРТЫ ==================

class MapWindow(BaseWindow):
    """
    Окно с картой, на которой отмечены кинотеатры.
    Использует библиотеку tkintermapview.
    """
    def setup_ui(self):
        self.window.geometry('800x600')
        # Создаём виджет карты
        map_widget = tkintermapview.TkinterMapView(self.window, width=800, height=600, corner_radius=0)
        map_widget.pack()

        # Центрируем карту на Екатеринбурге
        map_widget.set_position(56.89992921209157, 60.612832723260446)
        map_widget.set_zoom(11)

        # Добавляем маркеры для трёх кинотеатров
        map_widget.set_marker(56.89992921209157, 60.612832723260446, text='Премьер Зал Парк Хаус')
        map_widget.set_marker(56.79728684849465, 60.581814468466696, text='ККЦ "Премьер Зал Омега"')
        map_widget.set_marker(56.863124789835425, 60.63004649795355, text='ККЦ "Премьер Зал Гранат"')


# ================== ЗАПУСК ПРИЛОЖЕНИЯ ==================

if __name__ == '__main__':
    app = MainWindow()
    app.run()