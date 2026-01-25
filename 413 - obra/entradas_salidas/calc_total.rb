require 'csv'

# "date","hour in","hour out","name", "type"
# create a script tha treads the CSV and outputs all the days of the year from 2023-11-01 to 2025-11-30 with the total
# hours worked each day

def parse_csv(file_path)
  total_hours = Hash.new(0)

  CSV.foreach(file_path, headers: true) do |row|
    next if /obrero/i.match?(row['tipo'])

    date = Date.parse(row['fecha'])
    hour_in = row['ingreso'].to_f
    hour_out = row['egreso'].to_f

    # Calculate hours worked for the day
    hours_worked = hour_out - hour_in
    total_hours[date] += hours_worked if hours_worked > 0
  end

  total_hours
end

def generate_report(total_hours, start_date, end_date)
  report = []

  (start_date..end_date).each do |date|
    hours = total_hours[date] || 0
    report << "#{date}, #{hours.round(2)}"
  end

  report
end

def main
  file_path = 'todo.csv' # Adjust the path to your CSV file
  start_date = Date.new(2023, 11, 1)
  end_date = Date.new(2025, 11, 30)

  total_hours = parse_csv(file_path)
  report = generate_report(total_hours, start_date, end_date)

  puts 'Date, Total Hours Worked'
  puts report.join("\n")
end

if __FILE__ == $0
  require 'date'
  main
end
