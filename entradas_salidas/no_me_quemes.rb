require 'net/imap'

username = 'felix.cuello@gmail.com'
app_password = 'dwzd qdps vwaw unpx'

imap = Net::IMAP.new('imap.googlemail.com', ssl: true)
imap.port          => 993
imap.tls_verified? => true

imap.login(username, app_password)

imap.select('cardales')

# Define the date range
start_date = Date.new(2024, 1, 31)
end_date = Date.new(2024, 2, 1)

ingreso_emails = imap.search(['SUBJECT', 'de Ingreso', 'SINCE', start_date.strftime('%d-%b-%Y'), 'BEFORE', end_date.strftime('%d-%b-%Y')])
egreso_emails = imap.search(['SUBJECT', 'de Egreso', 'SINCE', start_date.strftime('%d-%b-%Y'), 'BEFORE', end_date.strftime('%d-%b-%Y')])
all_emails = (ingreso_emails + egreso_emails).uniq

hash_ingresos_egresos = {}
all_emails.each do |email_id|
  envelope = imap.fetch(email_id, 'ENVELOPE')[0].attr['ENVELOPE']

  # Fetch and display the email body if a suitable part is found
  body = imap.fetch(email_id, 'RFC822').first.attr["RFC822"]

  # ----------------- el body mal
  body.gsub!(/[\r\n]/, '')
  %r{ha (?<estado>.+?)<strong>(?<nombre>.*?)</strong> siendo las (?<hora>\d{2}:\d{2}) del.*? (?<dia>.+?)/(?<mes>.+?)/(?<ano>[^\s]+)} =~ body
  hora = hora.to_s.strip&.gsub(/=/, '')
  dia = dia.to_s.strip&.gsub(/=/, '')
  mes = mes.to_s.strip&.gsub(/=/, '')
  ano = ano.to_s.strip&.gsub(/=/, '')
  nombre = nombre.to_s.strip&.gsub(/=/, '')
  estado = estado.to_s.strip&.gsub(/=/, '')

  fecha = "#{ano}-#{mes}-#{dia}"

  hash_ingresos_egresos[fecha] ||= {}
  hash_ingresos_egresos[fecha][nombre] ||= {}
  hash_ingresos_egresos[fecha][nombre][estado] ||= hora
  print '.'
end

puts ''

puts 'fecha,hora de ingreso,hora de egreso,nombre'
hash_ingresos_egresos.keys.each do |fecha|
  hash_ingresos_egresos[fecha].keys.each do |nombre|
    puts "#{fecha}," \
      "#{hash_ingresos_egresos[fecha][nombre]['ingresado']}," \
      "#{hash_ingresos_egresos[fecha][nombre]['egresado']}," \
      "#{nombre}"
  end
end

imap.logout
imap.disconnect

