using LiveCharts;
using LiveCharts.Defaults;
using LiveCharts.Wpf;
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace INCVisualizer
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public string currentFilename;
        public List<string> states;
        public Func<double, string> YFormatter { get; set; }
        public double[,] rawData;
        public MainWindow()
        {
            InitializeComponent();

            currentFilename = null;

            SizeChanged += MainWindow_SizeChanged;

            mainChart.Hoverable = false;
            mainChart.DataTooltip = null;
            mainChart.DisableAnimations = true;

            states = new List<string>(new string[] { "up", "down", "left", "right" });
            YFormatter = value => (int)value==-2?"Disagree":(int)value==-1?"Agree":((int)value) == 0 || ((int)value) == 1 || ((int)value) == 2 || ((int)value) == 3?states[(int)value%states.Count]:"";

            addDummyData();
        }

        // Use the DataObject.Pasting Handler 
        private void TextBoxPasting(object sender, DataObjectPastingEventArgs e)
        {
            if (e.DataObject.GetDataPresent(typeof(String)))
            {
                String text = (String)e.DataObject.GetData(typeof(String));
                if (!IsTextAllowed(text))
                {
                    e.CancelCommand();
                }
            }
            else
            {
                e.CancelCommand();
            }
        }

        private static bool IsTextAllowed(string text)
        {
            Regex regex = new Regex("[^0-9.-]+"); //regex that matches disallowed text
            return !regex.IsMatch(text);
        }

        private void filterSize_PreviewTextInput(object sender, TextCompositionEventArgs e)
        {
            e.Handled = !IsTextAllowed(e.Text);
        }

        private void addDummyData()
        {
            mainChart.Series = new SeriesCollection
            {
                new StepLineSeries
                {
                    Title = "Series 1",
                    Values = new ChartValues<double> { 1,2,1,2,3 },
                    PointGeometry = null,
                    DataLabels = false
                },
                new StepLineSeries
                {
                    Title = "Series 2",
                    Values = new ChartValues<double> { 1,2,1,3,1 },
                    PointGeometry = null,
                    DataLabels = false
                }
            };
            
            DataContext = this;
        }

        private double[,] loadDataFromFile(string filename)
        {
            int skipHeaderLines = 1;
            int skipElements = 1;
            string rowDelim = "\n";
            string columnDelim = " ";
            int numElements = 0;
            StreamReader reader = new StreamReader(filename);
            string data = reader.ReadToEnd();
            reader.Close();
            string[] lines = data.Split(new string[] { rowDelim }, StringSplitOptions.RemoveEmptyEntries);
            double[,] output = output = new double[1,1];
            bool atLeastOne = false;
            for (int i = skipHeaderLines; i < lines.Length; i++)
            {
                string line = lines[i].Trim();
                string[] elements = line.Split(new string[] { columnDelim }, StringSplitOptions.RemoveEmptyEntries);
                if (i == skipHeaderLines)
                {
                    numElements = elements.Length - skipElements;
                    output = new double[numElements, lines.Length - skipHeaderLines];
                }
                if(elements.Length < numElements)
                {
                    MessageBox.Show("Error: There was an error in parsing a data row. There were insufficient elements in the row. The data will not be loaded", "Insufficient Columns in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                    return null;
                }
                for (int j = skipElements; j < numElements + skipElements; j++)
                    try
                    {
                        if (j == skipElements)
                            output[j - skipElements, i - skipHeaderLines] = double.Parse(elements[j]);
                        else
                            output[j - skipElements, i - skipHeaderLines] = states.IndexOf(elements[j]);
                        atLeastOne = true;
                    }
                    catch (Exception e)
                    {
                        if (e is ArgumentNullException)
                            MessageBox.Show("Error: There was a problem parsing an argument in the input file. The argument was found to be null or empty. The data will not be loaded.", "ArgumentNullException in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                        else if (e is FormatException)
                            MessageBox.Show("Error: There was a problem parsing an argument in the input file. The argument was not in the correct format. The data will not be loaded.", "FormatException in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                        else if (e is OverflowException)
                            MessageBox.Show("Error: There was a problem parsing an argument in the input file. The argument was larger or smaller than the maximum bounds of precision. The data will not be loaded.", "OverflowException in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                        else if (e is IndexOutOfRangeException)
                            MessageBox.Show("Error: There was a problem parsing an argument in the input file. Too many arguments in a row or column were found based on the initial data size scan. The data will not be loaded.", "IndexOutOfRangeException in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                        else
                            MessageBox.Show("Error: There was a problem parsing an argument in the input file. An unknown error occurred. The data will not be loaded.", e.ToString() + " in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                        return null;
                    }
            }
            if (!atLeastOne)
            {
                MessageBox.Show("Error: No data was found.", "Error in Data Loading", MessageBoxButton.OK, MessageBoxImage.Error);
                return null;
            }
            return output;
        }

        private string[] loadLabelsFromFile(string filename)
        {
            return new string[] { };
        }

        private void setData(double[,] data)
        {
            int numLabels = data.GetLength(0);
            string[] dummyLabels = new string[] { "", "Human", "Computer" };
            setData(dummyLabels, data);
        }
        private Tuple<double[,], int> filterData(double[,] data, double length, bool[] channels)
        {
            if (length <= 0) return new Tuple<double[,],int>(data,0);
            double hold = (length - 1) / length;
            double next = 1 / length;
            int changeCount = 0;
            for (int channel = 0; channel < data.GetLength(0); channel++) {
                if (!channels[channel]) continue;
                double mva = data[channel, 0];
                for (int i = 0; i < data.GetLength(1); i++)
                {
                    double val = data[channel, i];
                    mva = (mva * hold) + (val * next);
                    double newPoint = Math.Round(mva);
                    if (data[channel, i] != newPoint)
                        changeCount++;
                    data[channel, i] = newPoint;
                }
            }

            return new Tuple<double[,], int>(data, changeCount);
        }
        private void setData(string[] labels, double[,] data)
        {
            double filterLength = 1;
            try
            {
                filterLength = double.Parse(filterSize.Text); }
            catch (Exception) { }
            Tuple<double[,], int> filterResult = filterData(data, filterLength, new bool[] { false, false, true });
            data = filterResult.Item1;
            filterChange.Header = "Filtered Points: " + filterResult.Item2;
            StepLineSeries[] series = new StepLineSeries[labels.Length - 1];
            for(int i = 1; i < labels.Length; i++)
            {
                ChartValues<ObservablePoint> v = new ChartValues<ObservablePoint>();
                double prev = -1;
                for (int j = 0; j < data.GetLength(1); j++)
                {
                    if (data[i, j] == prev) continue;
                    v.Add(new ObservablePoint(data[0, j], data[i, j]));
                    prev = data[i, j];
                }
                series[i-1] = new StepLineSeries
                {
                    Title = labels[i],
                    Values = v,
                    PointGeometry = null,
                    DataLabels = false
                };
            }
            mainChart.Series = new SeriesCollection();
            for (int i = 0; i < series.Length; i++)
                mainChart.Series.Add(series[i]);

            ChartValues<ObservablePoint> vd = new ChartValues<ObservablePoint>();
            double prevd = -1;
            int agreeCount = 0;
            for (int i = 0; i < data.GetLength(1); i++) {
                double point = data[1, i] == data[2, i] ? -1 : -2;
                if (data[1, i] == data[2, i])
                    agreeCount++;
                if (point != prevd)
                    vd.Add(new ObservablePoint(data[0, i], point));
                prevd = point;
            }
            StepLineSeries diff = new StepLineSeries
            {
                Title = "Agreement",
                Values = vd,
                PointGeometry = null,
                DataLabels = false
            };
            mainChart.Series.Add(diff);

            agreementPercent.Header = "Agreement: " + ((double)agreeCount / (double)data.GetLength(1)).ToString("#.###");
        }

        private void MainWindow_SizeChanged(object sender, SizeChangedEventArgs e)
        {
            menu.Width = e.NewSize.Width;
            mainChart.Width = e.NewSize.Width - mainChart.Margin.Left - mainChart.Margin.Right - 50;
            mainChart.Height = e.NewSize.Height - mainChart.Margin.Top - mainChart.Margin.Bottom - 50;
        }

        private void MenuItem_Click(object sender, RoutedEventArgs e)
        {
            OpenFileDialog diag = new OpenFileDialog();
            diag.Multiselect = false;
            diag.CheckFileExists = true;
            diag.CheckPathExists = true;
            bool? result = diag.ShowDialog();
            if (result == null || result == false) return;
            currentFilename = diag.FileName;

            double[,] data = loadDataFromFile(currentFilename);
            if (data == null)
            {
                currentFilename = null;
                return;
            }
            else
            {
                rawData = data;
                setData(data);
            }
        }

        private void MenuItem_Click_1(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private void Button_Click(object sender, RoutedEventArgs e)
        {
            if (currentFilename == null) return;
            setData(rawData);
        }
    }
}
