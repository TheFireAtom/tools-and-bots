// Подключение необходимых библиотек
#include <iostream>
#include <complex>
#include <vector>
#include <cmath>

const double PI = acos(-1); // Константа Пи задаётся с помощью арккосинуса от -1

// Реализаия алгоритма Кули — Тьюки с помощью рекурсии
void fft(std::vector<std::complex<double>>& signal) {
    int N = signal.size();
    if (N <= 1) return;

    // Разделение исходного сигнала на чётную и нечётную часть
    std::vector<std::complex<double>> even, odd;
    for (int i = 0; i < N; i += 2) {
        even.push_back(signal[i]);
        odd.push_back(signal[i + 1]);
    }

    // Рекурсия БПФ для чётной и нечётной части
    fft(even);
    fft(odd);

    // Соединение результатов
    for (int k = 0; k < N / 2; ++k) {
        // Функция polar создает комплексное число на основе полярных координат, в качестве аргументов принимаются значение амплитуды и фазы
        std::complex<double> t = std::polar(1.0, -2 * PI * k / N) * odd[k]; 
        // Релизация алоритма "бабочки", который позволяет ещё больше оптимизировать работу алгоритма
        signal[k] = even[k] + t;
        signal[k + N / 2] = even[k] - t;
    }
}

// Создание исходного сигнала на основе необходимой функции
void generateSignal(std::vector<double>& signal, double fs) {
    const double ts = 1.0 / fs;
    for (size_t n = 0; n < signal.size(); ++n) {
        signal[n] = 1.5 * std::cos(2 * PI * 1500 * n * ts + (PI / 4)) +
            0.25 * std::cos(2 * PI * 1600 * n * ts + (PI / 2)) +
            1 * std::cos(2 * PI * 4500 * n * ts + (PI / 4));
    }
}


// Основная функция с заданными исходными данными 
int main() {
    // Значение N = 4096 было выбрано чтобы продемонстрировать скорость работы алгоритма
    // Для реализаии алгоритма необходимо, чтобы количество отсчётов соответствовало степени двойки
    const int N = 4096; // Количество отсчётов 
    const double fs = 18000.0; // Частота дискретизации
     
    // Создание вектора (динамического массива) с размером в N единиц
    std::vector<double> signal(N);
    // Вызов функции генераии сигнала, в качестве аргументов заданы массив signal и частота дискретизации fs
    generateSignal(signal, fs);

    // Переприсваивание значений массива signal в массив с комплексными значениями complex_signal
    std::vector<std::complex<double>> complex_signal(N);
    for (int i = 0; i < N; ++i) {
        complex_signal[i] = signal[i];
    }

    // Вызов функции БПФ для подсчёта значений в массиве complex_signal
    fft(complex_signal);

    // Вывод полученных результатов
    for (int i = 0; i < N; ++i) {
        std::cout << "FFT[" << i << "] = " << complex_signal[i] << std::endl;
    }

    return 0;
}
