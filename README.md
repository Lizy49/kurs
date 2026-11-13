```cpp
using System;
using System.Windows.Forms;

namespace ArrayStatisticsApp
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        // Обработчик нажатия на кнопку
        private void btnAnalyze_Click(object sender, EventArgs e)
        {
            lstOutput.Items.Clear(); // Очищаем старые результаты

            string input = txtInput.Text.Trim();

            // Проверка на пустую строку
            if (string.IsNullOrEmpty(input))
            {
                MessageBox.Show("Введите числа!", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Разбиваем строку на массив строк по пробелам
            string[] stringNumbers = input.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);

            // Создаем массив целых чисел
            int[] numbers = new int[stringNumbers.Length];

            try
            {
                // Пытаемся преобразовать строки в числа
                for (int i = 0; i < stringNumbers.Length; i++)
                {
                    numbers[i] = int.Parse(stringNumbers[i]);
                }

                // Вызываем наш пользовательский метод и получаем кортеж с результатами
                var result = AnalyzeArray(numbers);

                // Выводим результаты в ListBox
                lstOutput.Items.Add($"Минимум: {result.Min}");
                lstOutput.Items.Add($"Максимум: {result.Max}");
                lstOutput.Items.Add($"Сумма: {result.Sum}");
                lstOutput.Items.Add($"Среднее арифметическое: {result.Average:F2}"); // F2 - округление до 2 знаков
                lstOutput.Items.Add("-----------------------------");
                lstOutput.Items.Add($"Количество четных: {result.EvenCount}");
                lstOutput.Items.Add($"Количество нечетных: {result.OddCount}");
            }
            catch (FormatException)
            {
                // Обработка исключения, если ввели буквы вместо чисел
                MessageBox.Show("Ошибка ввода! Пожалуйста, вводите только целые числа, разделенные пробелом.", 
                                "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            catch (Exception ex)
            {
                // Обработка других непредвиденных ошибок
                MessageBox.Show($"Произошла ошибка: {ex.Message}", "Ошибка");
            }
        }

        // ПОЛЬЗОВАТЕЛЬСКИЙ МЕТОД (вынесен за пределы кнопки)
        // Возвращает кортеж (tuple) с результатами
        private (int Min, int Max, int Sum, double Average, int EvenCount, int OddCount) AnalyzeArray(int[] arr)
        {
            // Инициализируем переменные
            int min = arr[0];
            int max = arr[0];
            int sum = 0;
            int evenCount = 0;
            int oddCount = 0;

            // Проходимся по массиву циклом
            foreach (int num in arr)
            {
                if (num < min) min = num;
                if (num > max) max = num;
                sum += num;

                // Проверка на четность/нечетность
                if (num % 2 == 0)
                    evenCount++;
                else
                    oddCount++;
            }

            // Вычисляем среднее арифметическое (явно приводим к double, чтобы не было целочисленного деления)
            double average = (double)sum / arr.Length;

            // Возвращаем результат в виде кортежа
            return (min, max, sum, average, evenCount, oddCount);
        }
    }
}
```
