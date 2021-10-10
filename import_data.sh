psql << EOF
\connect coolgeo
copy postal_codes FROM '$PWD/postal_codes.csv' CSV HEADER;
copy paystats FROM '$PWD/paystats.csv' CSV HEADER;
EOF
