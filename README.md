```cpp
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using System.Windows.Forms.DataVisualization.Charting;

namespace BankDepositApp
{
    public partial class Form1 : Form
    {
        // Класс для хранения данных по одному году (для таблицы и графика)
        public class YearData
        {
            public int Year { get; set; }
            public decimal StartSum { get; set; }
            public decimal Interest { get; set; }
            public decimal EndSum { get; set; }
        }

        // Переменные для анимации таймера
        private List<YearData> dataWithAdd = new List<YearData>();
        private List<YearData> dataWithoutAdd = new List<YearData>();
        private int animationStep = 0;

        public Form1()
        {
            InitializeComponent();
            SetupChart();
            numMonthlyAdd.Enabled = false; // Изначально пополнение выключено
            timer1.Tick += Timer1_Tick; // Подписываемся на событие таймера
            trackBarRate.Scroll += TrackBarRate_Scroll; // Подписываемся на прокрутку TrackBar
        }

        // Настройка внешнего вида графика при запуске
        private void SetupChart()
        {
            chart1.Series.Clear();
            chart1.ChartAreas[0].AxisX.Title = "Годы";
            chart1.ChartAreas[0].AxisY.Title = "Сумма (руб.)";
            
            // Линия с пополнением
            Series seriesWith = new Series("С пополнением");
            seriesWith.ChartType = SeriesChartType.Line;
            seriesWith.BorderWidth = 3;
            chart1.Series.Add(seriesWith);

            // Линия без пополнения
            Series seriesWithout = new Series("Без пополнения");
            seriesWithout.ChartType = SeriesChartType.Line;
            seriesWithout.BorderWidth = 3;
            seriesWithout.Color = Color.Red;
            chart1.Series.Add(seriesWithout);
        }

        // Обработчик нажатия на чекбокс (включает/выключает поле ввода пополнения)
        private void chkMonthlyAdd_CheckedChanged(object sender, EventArgs e)
        {
            numMonthlyAdd.Enabled = chkMonthlyAdd.Checked;
        }

        // Обработчик кнопки "Рассчитать"
        private void btnCalculate_Click(object sender, EventArgs e)
        {
            try
            {
                // Считываем данные из полей
                decimal startSum = numStartSum.Value;
                double rate = (double)numRate.Value;
                int years = (int)numYears.Value;
                bool hasAdd = chkMonthlyAdd.Checked;
                decimal monthlyAdd = numMonthlyAdd.Value;

                // Валидация (проверка на дурака)
                if (startSum <= 0) throw new Exception("Начальная сумма должна быть больше нуля!");
                if (years <= 0) throw new Exception("Количество лет должно быть больше нуля!");

                // Вызов пользовательских методов (вынесены за пределы кнопки)
                dataWithoutAdd = CalculateDeposit(startSum, rate, years, false, 0);
                dataWithAdd = CalculateDeposit(startSum, rate, years, hasAdd, monthlyAdd);

                // Вывод в DataGridView (берем расчет с пополнением, если стоит галочка, иначе без)
                var displayData = hasAdd ? dataWithAdd : dataWithoutAdd;
                dataGridView1.DataSource = null;
                dataGridView1.DataSource = displayData;

                // Настраиваем заголовки таблицы
                dataGridView1.Columns["Year"].HeaderText = "Год";
                dataGridView1.Columns["StartSum"].HeaderText = "Сумма на начало";
                dataGridView1.Columns["Interest"].HeaderText = "Проценты";
                dataGridView1.Columns["EndSum"].HeaderText = "Сумма на конец";

                // Обновляем график
                DrawChart(dataWithAdd, dataWithoutAdd);

                // Обновляем статусную строку
                UpdateStatusStrip(dataWithAdd, dataWithoutAdd, hasAdd);

                // Запускаем анимацию
                animationStep = 0;
                timer1.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка: {ex.Message}", "Ошибка ввода", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // --- ПОЛЬЗОВАТЕЛЬСКИЕ МЕТОДЫ ---

        // 1. Метод расчета сложного процента по годам
        private List<YearData> CalculateDeposit(decimal start, double rate, int years, bool hasAdd, decimal monthlyAdd)
        {
            List<YearData> result = new List<YearData>();
            decimal currentSum = start;

            for (int i = 1; i <= years; i++)
            {
                decimal startOfYear = currentSum;
                // Формула сложного процента за год
                decimal interest = currentSum * ((decimal)rate / 100);
                currentSum += interest;

                // Если включено пополнение, добавляем сумму за 12 месяцев в конце года
                if (hasAdd)
                {
                    currentSum += monthlyAdd * 12;
                }

                result.Add(new YearData
                {
                    Year = i,
                    StartSum = Math.Round(startOfYear, 2),
                    Interest = Math.Round(interest, 2),
                    EndSum = Math.Round(currentSum, 2)
                });
            }
            return result;
        }

        // 2. Метод отрисовки графика
        private void DrawChart(List<YearData> withAdd, List<YearData> withoutAdd)
        {
            chart1.Series["С пополнением"].Points.Clear();
            chart1.Series["Без пополнения"].Points.Clear();

            // Ограничиваем количество точек для анимации (если запущен таймер)
            int limit = (animationStep == 0 || animationStep > withoutAdd.Count) ? withoutAdd.Count : animationStep;

            for (int i = 0; i < limit; i++)
            {
                chart1.Series["С пополнением"].Points.AddXY(withAdd[i].Year, withAdd[i].EndSum);
                chart1.Series["Без пополнения"].Points.AddXY(withoutAdd[i].Year, withoutAdd[i].EndSum);
            }
        }

        // 3. Метод обновления нижней панели (StatusStrip)
        private void UpdateStatusStrip(List<YearData> withAdd, List<YearData> withoutAdd, bool hasAdd)
        {
            var finalData = hasAdd ? withAdd.Last() : withoutAdd.Last();
            decimal totalIncome = finalData.EndSum - numStartSum.Value;

            lblTotalSum.Text = $"Итоговая сумма: {finalData.EndSum:C2}";
            lblTotalIncome.Text = $" | Общий доход: {totalIncome:C2}";
        }

        // 4. Метод сохранения в CSV (для усложнения из меню)
        private void SaveToCSV()
        {
            using (SaveFileDialog sfd = new SaveFileDialog() { Filter = "CSV файл|*.csv" })
            {
                if (sfd.ShowDialog() == DialogResult.OK)
                {
                    try
                    {
                        using (StreamWriter sw = new StreamWriter(sfd.FileName))
                        {
                            // Заголовки
                            sw.WriteLine("Год;Сумма на начало;Проценты;Сумма на конец");
                            // Данные (берем из таблицы)
                            foreach (DataGridViewRow row in dataGridView1.Rows)
                            {
                                if (row.Cells[0].Value != null)
                                {
                                    sw.WriteLine($"{row.Cells[0].Value};{row.Cells[1].Value};{row.Cells[2].Value};{row.Cells[3].Value}");
                                }
                            }
                        }
                        MessageBox.Show("Файл успешно сохранен!", "Успех", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Ошибка сохранения: {ex.Message}");
                    }
                }
            }
        }


        // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

        // Событие изменения значения на TrackBar (меняет ставку в реальном времени)
        private void TrackBarRate_Scroll(object sender, EventArgs e)
        {
            numRate.Value = trackBarRate.Value;
            if (numStartSum.Value > 0 && numYears.Value > 0)
            {
                btnCalculate_Click(null, null); // Автоматический пересчет
            }
        }

        // Событие таймера (для анимации "нарастания" графика)
        private void Timer1_Tick(object sender, EventArgs e)
        {
            animationStep++;
            if (animationStep >= dataWithoutAdd.Count)
            {
                timer1.Stop(); // Останавливаем таймер, когда график достроен
            }
            DrawChart(dataWithAdd, dataWithoutAdd); // Перерисовываем с новым шагом
        }

        // Обработчик меню "Сохранить в CSV"
        private void saveToCsvToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (dataGridView1.Rows.Count > 0)
                SaveToCSV();
            else
                MessageBox.Show("Сначала выполните расчет!", "Внимание");
        }
    }
}
```
