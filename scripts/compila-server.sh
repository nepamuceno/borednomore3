cd ~/desar2
unzip -o ../desar-server-full.zip
rm -rf desar-server
mv desar-server-new desar-server
cd desar-server
rm -f data/admin.db data/company_admin.db
go mod tidy
make run
