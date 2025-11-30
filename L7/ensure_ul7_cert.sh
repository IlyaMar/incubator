#!/bin/zsh -e


function check_salt() {
    filter=$2
    app=$1
    for host in $(pssh list ${filter?}); do
        pssh run --cause other:check "keytool -list -keystore /etc/yc/${app?}/truststore | grep yandex-cloud-ul7" $host
    done
}


function check_kten() {
    app=$1
    ct=$2
    echo "checking $app"
    kubectl -n iam get pods -lapp.kubernetes.io/name=${app?} -o name | xargs -I {} kubectl -n iam exec {} -c ${ct?} -- keytool -list -storepass changeit -keystore /etc/yc/${ct?}/cacerts 2>/dev/null | grep ul7
}

function use_context() {
    env=${1?}
    zone=${2?}
    kubectl config use-context ${env?}-${zone?}-svm 
}

function check_kten_all() {
    env=$1
    app=$2
    ct=$3

    for zone in a b d; do
        use_context $env $zone
        check_kten $app $ct
    done
}

function check_salt_all() {
    domain=$1
    app_full=$2
    app_short=$3

    eval "check_salt ${app_full?} 'x@${app_short?}-*.svc.${domain?}'"
}


# check_kten_all prod quota-manager quota-manager
# check_kten_all kz quota-manager quota-manager

# check_kten_all preprod iam-oslogin-service oslogin-service
# check_kten_all  prod iam-oslogin-service oslogin-service
check_kten_all  kz iam-oslogin-service oslogin-service


# org-service, control-plane, reaper, openid-server, token-service и activeprobes

# check_salt_all cloud.yandex.net org-service iam-org
# check_salt_all cloud.yandex.net iam-control-plane iam-cp
# check_salt_all cloud.yandex.net resource-manager iam-reaper
# check_salt_all cloud.yandex.net openid-server iam-openid
# check_salt_all cloud.yandex.net token-service iam-ts

# check_salt_all yacloudkz.tech org-service iam-org
# check_salt_all yacloudkz.tech iam-control-plane iam-cp
# check_salt_all yacloudkz.tech resource-manager iam-reaper
# check_salt_all yacloudkz.tech openid-server iam-openid
# check_salt_all yacloudkz.tech token-service iam-ts



# check_salt_all yacloudkz.tech rm-control-plane iam-rm