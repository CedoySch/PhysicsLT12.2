import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox, QTextEdit, QSizePolicy,
    QGroupBox, QGridLayout, QLineEdit, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ElectrostaticFieldApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Визуализация электростатического поля и эквипотенциалов')
        self.setGeometry(100, 100, 1400, 800)

        # Инструкции
        instructions_label = QLabel('Введите параметры зарядов (x y q) в каждой строке:')
        instructions_label.setAlignment(Qt.AlignLeft)

        # Поле ввода зарядов
        self.charges_input = QTextEdit()
        self.charges_input.setPlaceholderText("Пример:\n0 0 1\n1 0 -1")
        self.charges_input.setFixedHeight(150)

        # Группа параметров сетки
        grid_group = QGroupBox("Параметры сетки")
        grid_layout = QGridLayout()

        self.grid_min_input = QLineEdit("-10")
        self.grid_max_input = QLineEdit("10")
        self.grid_points_input = QLineEdit("200")

        grid_layout.addWidget(QLabel("Мин X и Y:"), 0, 0)
        grid_layout.addWidget(self.grid_min_input, 0, 1)
        grid_layout.addWidget(QLabel("Макс X и Y:"), 1, 0)
        grid_layout.addWidget(self.grid_max_input, 1, 1)
        grid_layout.addWidget(QLabel("Количество точек:"), 2, 0)
        grid_layout.addWidget(self.grid_points_input, 2, 1)

        grid_group.setLayout(grid_layout)

        # Группа параметров эквипотенциалов
        potential_group = QGroupBox("Параметры эквипотенциалов")
        potential_layout = QGridLayout()

        self.show_potential_checkbox = QCheckBox("Отображать эквипотенциальные линии")
        self.show_potential_checkbox.setChecked(True)
        potential_layout.addWidget(self.show_potential_checkbox, 0, 0, 1, 2)

        potential_layout.addWidget(QLabel("Количество уровней:"), 1, 0)
        self.potential_levels_spinbox = QSpinBox()
        self.potential_levels_spinbox.setRange(1, 100)
        self.potential_levels_spinbox.setValue(20)
        potential_layout.addWidget(self.potential_levels_spinbox, 1, 1)

        potential_group.setLayout(potential_layout)

        # Кнопка построения
        self.plot_button = QPushButton('Построить поле')
        self.plot_button.clicked.connect(self.plot_field)

        # Поле для графика
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()

        # Подключение событий мыши
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

        # Компоновка ввода
        input_layout = QVBoxLayout()
        input_layout.addWidget(instructions_label)
        input_layout.addWidget(self.charges_input)
        input_layout.addWidget(grid_group)
        input_layout.addWidget(potential_group)
        input_layout.addWidget(self.plot_button)
        input_layout.addStretch()

        # Основная компоновка
        main_layout = QHBoxLayout()
        main_layout.addLayout(input_layout, 1)
        main_layout.addWidget(self.canvas, 3)

        self.setLayout(main_layout)
        self.show()

    def plot_field(self):
        try:
            charges_text = self.charges_input.toPlainText().strip()
            if not charges_text:
                raise ValueError("Необходимо ввести хотя бы один заряд.")

            # Парсинг зарядов
            charges = []
            for idx, line in enumerate(charges_text.split('\n'), start=1):
                if not line.strip():
                    continue
                parts = line.strip().split()
                if len(parts) != 3:
                    raise ValueError(f"Строка {idx}: Ожидается три значения (x y q).")
                x_str, y_str, q_str = parts
                try:
                    x, y, q = float(x_str), float(y_str), float(q_str)
                except ValueError:
                    raise ValueError(f"Строка {idx}: x, y и q должны быть числами.")
                charges.append((x, y, q))

            if not charges:
                raise ValueError("Необходимо ввести хотя бы один заряд.")

            # Парсинг параметров сетки
            try:
                grid_min = float(self.grid_min_input.text())
                grid_max = float(self.grid_max_input.text())
                grid_points = int(self.grid_points_input.text())
                if grid_min >= grid_max:
                    raise ValueError("Мин должно быть меньше Макс.")
                if grid_points <= 0:
                    raise ValueError("Количество точек должно быть положительным.")
            except ValueError as ve:
                raise ValueError(f"Параметры сетки: {ve}")

            # Параметры эквипотенциалов
            show_potential = self.show_potential_checkbox.isChecked()
            potential_levels = self.potential_levels_spinbox.value()

            # Создание сетки
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)  # Храним ось для взаимодействия
            ax = self.ax

            x = np.linspace(grid_min, grid_max, grid_points)
            y = np.linspace(grid_min, grid_max, grid_points)
            X, Y = np.meshgrid(x, y)
            Ex = np.zeros_like(X)
            Ey = np.zeros_like(Y)
            V = np.zeros_like(X)

            # Вычисление полей и потенциала
            for charge in charges:
                x0, y0, q = charge
                dx = X - x0
                dy = Y - y0
                r_squared = dx**2 + dy**2
                r_squared[r_squared == 0] = 1e-20
                r = np.sqrt(r_squared)
                Ex += q * dx / (r_squared * r)
                Ey += q * dy / (r_squared * r)
                V += q / r

            # Визуализация линий напряженности
            ax.streamplot(X, Y, Ex, Ey, color='k', density=1.5, linewidth=0.5, arrowsize=1)

            # Визуализация эквипотенциалов
            if show_potential:
                V_min, V_max = np.min(V), np.max(V)
                if V_min == V_max:
                    V_min -= 1
                    V_max += 1
                levels = np.linspace(V_min, V_max, potential_levels)
                potential_contours = ax.contour(X, Y, V, levels=levels, cmap='viridis', alpha=0.7)
                ax.clabel(potential_contours, inline=True, fontsize=8, fmt="%.2f")

            # Отображение зарядов
            for charge in charges:
                x0, y0, q = charge
                color = 'ro' if q > 0 else 'bo'
                ax.plot(x0, y0, color, markersize=8)

            ax.set_xlim(grid_min, grid_max)
            ax.set_ylim(grid_min, grid_max)
            ax.set_aspect('equal')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_title('Электростатическое поле и эквипотенциалы')
            ax.grid(True)

            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def on_scroll(self, event):
        """Обработчик для масштабирования графика с учетом границ сетки."""
        ax = self.ax
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # Задаем границы сетки
        grid_min = float(self.grid_min_input.text())
        grid_max = float(self.grid_max_input.text())

        # Текущий центр и размеры
        x_range = (x_max - x_min) / 2
        y_range = (y_max - y_min) / 2
        x_center = (x_max + x_min) / 2
        y_center = (y_max + y_min) / 2

        # Определяем коэффициент масштабирования
        scale_factor = 1.2 if event.button == 'up' else 0.8

        # Новые размеры с учетом масштабирования
        new_x_range = x_range * scale_factor
        new_y_range = y_range * scale_factor

        # Ограничиваем новые границы сеткой
        new_x_min = max(grid_min, x_center - new_x_range)
        new_x_max = min(grid_max, x_center + new_x_range)
        new_y_min = max(grid_min, y_center - new_y_range)
        new_y_max = min(grid_max, y_center + new_y_range)

        # Если новые границы слишком малы, предотвращаем масштабирование
        if (new_x_max - new_x_min) < 1e-2 or (new_y_max - new_y_min) < 1e-2:
            return

        # Устанавливаем новые границы
        ax.set_xlim([new_x_min, new_x_max])
        ax.set_ylim([new_y_min, new_y_max])

        # Обновляем график
        self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    ex = ElectrostaticFieldApp()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
