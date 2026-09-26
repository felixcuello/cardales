#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require 'open-uri'
require 'pdf-reader'
require 'stringio'

# Columnas a incluir en el CSV, en este orden.
# Claves disponibles: :socio, :nombre, :monto, :meses, :judicializado
COLUMNS = %i[socio nombre monto meses judicializado].freeze

HEADERS = {
  socio: 'Socio',
  nombre: 'Apellido y Nombre',
  monto: 'Monto de deuda',
  meses: 'Meses de deuda',
  judicializado: 'Judicializado'
}.freeze

SOCIO_LINE = /\A\s*(\d{5}-\d{2})\s+(.*)\z/

def parse_amount(raw)
  return 0 if raw.nil? || raw.strip == '-'

  raw.gsub('.', '').to_i
end

def count_months(amount_tokens)
  periods = amount_tokens[0...-1]
  return nil if periods.empty?

  periods.count { |raw| raw != '-' }
end

def parse_row(line)
  match = line.match(SOCIO_LINE)
  return nil unless match

  socio = match[1]
  rest = match[2]
  amounts = rest.scan(/\$\s*([\d.]+|-)/).flatten
  return nil if amounts.empty?

  total_raw = amounts.last
  return nil if total_raw == '-'

  nombre = rest.split('$', 2).first
               .sub(/\A[\d\s\-]*\s*/, '')
               .gsub(/\s+/, ' ')
               .strip
  return nil if nombre.empty?

  {
    socio: socio,
    nombre: nombre,
    monto: parse_amount(total_raw),
    meses: count_months(amounts)
  }
end

def extract_deudores(pdf_io)
  judicializado = false
  rows = []

  PDF::Reader.new(pdf_io).pages.each do |page|
    page.text.each_line(chomp: true) do |line|
      if line.match?(/NO JUDICIALIZADOS|EXTRAJUDICIAL/i)
        judicializado = false
      elsif line.match?(/DEUDORES JUDICIALIZADOS/i)
        judicializado = true
      end

      row = parse_row(line)
      next unless row

      row[:judicializado] = judicializado ? 'Sí' : 'No'
      rows << row
    end
  end

  rows
end

url = ARGV[0]
abort 'Uso: ruby deudores.rb URL [salida.csv]' if url.to_s.empty?

rows = extract_deudores(StringIO.new(URI.open(url, 'rb').read))

csv = CSV.generate(encoding: 'UTF-8') do |out|
  out << COLUMNS.map { |key| HEADERS.fetch(key) }
  rows.each { |row| out << COLUMNS.map { |key| row[key] } }
end

if ARGV[1]
  File.write(ARGV[1], csv)
else
  print csv
end
