createdb coolgeo
echo "CREATE USER $USER_RWX PASSWORD '$PASS_RWX_ENC'" 
echo "CREATE USER $USER_RX PASSWORD '$PASS_RX_ENC'" 
echo "CREATE USER $USER_RWX PASSWORD '$PASS_RWX_ENC'" | psql
echo "CREATE USER $USER_RX PASSWORD '$PASS_RX_ENC'" | psql
