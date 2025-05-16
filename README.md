
运行服务器
pushd www; python -m http.server; popd
访问
http://localhost:8000/
标注模式访问（id与/img/full中对应）
http://localhost:8000/draw/index.html?annotate=1&id=1
生成vptree
cd /www/data
node index.js
