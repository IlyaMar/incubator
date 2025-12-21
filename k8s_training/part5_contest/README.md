clan pod ---> silo : HTTP PUT clan=atreides

# Prepare
kubectl create ns dune

## build image - spice silo

docker build . -t iam-k8s-training/spice-resource-silo:1.4
iam-k8s-training/spice-resource-silo:1.0

cd ~/cloudia-deploy/cloud/iam/terraform/mk8s/misc/
vim copy_images.sh
copy_image_to_repo iam-k8s-training/spice-resource-silo:1.4 iam-k8s-training/spice-resource-silo:1.4 cr.cloud-preprod.yandex.net/crtqchh33vmh7gjrr5uq 


## build image - harvester

docker pull python:3.8-slim

copy_image_to_repo cr.cloud-preprod.yandex.net/crtqchh33vmh7gjrr5uq/python:3.8-slim-user1000 python:3.8-slim-user1000 cr.cloud-preprod.yandex.net/crtqchh33vmh7gjrr5uq


# Run

kubectl exec $(kubectl get pod -l team=atreides --output=jsonpath={.items..metadata.name}) -- curl -X PUT -v 'http://resource-silo:8080/deliver?clan=atreides'

# custom image
dockerfile:
```
...
# Use the non-root user with numeric ID
USER 1000:1000
```

docker build . -t cr.cloud-preprod.yandex.net/crtqchh33vmh7gjrr5uq/your_image:1.0

```
yc config profile activate preprod
docker push cr.cloud-preprod.yandex.net/crtqchh33vmh7gjrr5uq/your_image:1.0
```
