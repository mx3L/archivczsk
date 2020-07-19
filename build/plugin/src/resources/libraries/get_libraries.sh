#!/bin/sh

script_path="`dirname \"$0\"`"
tmp_path=/tmp/archivczsk_libs


module_available()
{
    #python -c "import sys;sys.path.append("\"\.\/$1\"");import $1" 2> /dev/null
    #if [ $? -eq 0 ]; then
    if [ -d $1 ]; then
        if [ "$2" = "f" ]; then
            echo "0"
        else
            echo "1"
        fi
    else
        echo "0"
    fi
}

install_demjson()
{
    demjson_url="https://files.pythonhosted.org/packages/96/67/6db789e2533158963d4af689f961b644ddd9200615b8ce92d6cad695c65a/demjson-2.2.4.tar.gz"

    local installed="0"
    curl -L $demjson_url -o $tmp_path/demjson.tar.gz && 2> /dev/null \
    tar xzf $tmp_path/demjson.tar.gz -C $tmp_path && \
    rm -rf $script_path/demjson 2> /dev/null && \
    mkdir -p $script_path/demjson 2> /dev/null || true && \
    cp $tmp_path/demjson-2.2.4/demjson.py $script_path/demjson && \
    touch $script_path/demjson/__init__.py && \
    installed="1"

    echo $installed
}

install_youtube_dl()
{
    youtubedl_url="https://files.pythonhosted.org/packages/51/80/d3938814a40163d3598f8a1ced6abd02d591d9bb38e66b3229aebe1e2cd0/youtube_dl-2020.5.3.tar.gz"

    local installed="0"
    curl -L $youtubedl_url -o $tmp_path/youtube_dl.tar.gz 2> /dev/null && \
    tar xzf $tmp_path/youtube_dl.tar.gz -C $tmp_path && \
    rm -rf $script_path/youtube_dl 2> /dev/null && \
    cp -rf $tmp_path/youtube_dl-2020.5.3/youtube_dl $script_path && \
    installed="1"

    echo $installed
}

check_module()
{
res=$(module_available $1 $2)
if [ $res = "0" ]; then
    echo "**************************************"
    echo "$1 nie je nainstalovany, instalujem..."
    echo "**************************************"
    echo ""
    res=$(install_$1)
    if [ $res = "1" ]; then
        echo ""
        echo "**************************************"
        echo "$1 bol uspesne nainstalovany"
        echo "**************************************"
    else
        echo ""
        echo "**************************************"
        echo "$1 nebol nainstalovany"
        echo "**************************************"
    fi
else
    echo "**************************************"
    echo "$1 je nainstalovany"
    echo "**************************************"
    echo ""
fi
}

cd $script_path

mkdir -p $tmp_path 2> /dev/null

check_module demjson $1
check_module youtube_dl $1

rm -rf $tmp_path 2> /dev/null

exit 0
