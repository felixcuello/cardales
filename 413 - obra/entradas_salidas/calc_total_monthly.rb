require 'csv'

# "date","hour in","hour out","name", "type"
# create a script that reads the CSV and outputs all the months from 2023-11-01 to 2025-11-30 with the total
# hours worked each month

def parse_csv_by_month(file_path)
  monthly_hours = Hash.new(0)

  CSV.foreach(file_path, headers: true) do |row|
    next if /obrero/i.match?(row['tipo'])

    date = Date.parse(row['fecha'])
    hour_in = row['ingreso'].to_f
    hour_out = row['egreso'].to_f

    # Calculate hours worked for the day
    hours_worked = hour_out - hour_in
    if hours_worked > 0
      # Group by year-month
      month_key = Date.new(date.year, date.month, 1)
      monthly_hours[month_key] += hours_worked
    end
  end

  monthly_hours
end

def generate_monthly_report(monthly_hours, start_date, end_date)
  report = []

  # Generate all months between start and end date
  current_month = Date.new(start_date.year, start_date.month, 1)
  end_month = Date.new(end_date.year, end_date.month, 1)

  while current_month <= end_month
    hours = monthly_hours[current_month] || 0
    report << "#{current_month.strftime('%Y-%m')}, #{hours.round(2)}"

    # Move to next month
    current_month = current_month.next_month
  end

  report
end

def main
  file_path = 'todo.csv' # Adjust the path to your CSV file
  start_date = Date.new(2023, 11, 1)
  end_date = Date.new(2025, 11, 30)

  monthly_hours = parse_csv_by_month(file_path)
  report = generate_monthly_report(monthly_hours, start_date, end_date)

  puts 'Month, Total Hours Worked'
  puts report.join("\n")
end

if __FILE__ == $0
  require 'date'
  main
end
