---
layout: post
date: 2020-06-02
title: Azar Mirror 서버 제작기 2편 - Istio와 함께하는 Traffic Mirroring
author: sammie
tags: microservice istio mirror traffic virtualservice kubernetes
excerpt: Mirror 서버로 traffic을 복제하고, microservice를 사용하는 요청을 routing하기 위해 Istio를 사용한 경험을 공유합니다.
last_modified_at: 2020-06-02
---

안녕하세요, DevOps 팀의 Sammie입니다. Mirror 서버를 만들기 위해 Istio[[1]](https://istio.io/)를 사용하여 traffic을 복제하고, routing 한 방법에 대해 좀 더 자세하게 공유해 드리려고 이 글을 작성했습니다 :)

평화롭던(?) 어느 날, Backend Dev 1팀의 Fitz님이 Azar 서버 테스트를 더 쉽게 하기 위해 mirror 서버를 만들어보자고 했습니다. Mirror 서버를 만들기 위해 DevOps 팀에서 처리해야 할 일을 정하고, 어떻게 할 수 있을지 다양한 방법을 검토한 끝에 mirror 서버를 완성 할 수 있었습니다. 왜 mirror 서버가 필요했는지, 목표가 무엇인지, 왜 이런 작업이 필요했는지는 Fitz님이 [Azar Mirror 서버 제작기 1편](https://hyperconnect.github.io/2020/05/15/azar-mirror-1.html)에 상세하게 설명해 놓았습니다. 이 글을 읽기 전에, 1편을 먼저 읽으면 이해하기 좀 더 쉬울 것입니다.

본격적인 글의 시작에 앞서, Istio는 빠르게 성장하는 프로젝트인 만큼 버전별로 지원하는 기능이 빠르게 바뀌거나, 동작이 달라질 수 있어 유의하시기 바랍니다. Azar test 서버와 mirror 서버는 1.4.x를 사용하고 있어 이 글의 모든 내용은 1.4에 맞춰 작성되었습니다. 또한 Kubernetes[[2]](https://kubernetes.io/)와 Istio에 대한 기본적인 지식에 대해서는 별도로 설명하지 않았습니다. Pod, Service, Namespace, Istio VirtualService에 대해서 알지 못하신다면 Kubernetes와 Istio 문서를 참고하시기 바랍니다.


# Tasks To Do
Azar Mirror 서버 제작기 1편에서 소개했던 4가지의 요구사항을 해결해야 합니다. 그중 DevOps 팀에서 처리해야 할 사항은 크게 2가지입니다.

### 1. **Test API 서버** inbound traffic 복제
추가적인 설명이 필요 없는 자명한 요구사항입니다. **Test API 서버**의 inbound HTTP traffic을 빠짐없이 복제해서 **mirror API 서버**로 보내면 됩니다.

### 2. Microservice outbound http call 처리
Azar 서버는 microservice 구조로 되어 있어, **API 서버**는 일부 요청을 처리하기 위해 microservice로 outbound http call을 합니다. **Mirror API 서버**를 만드는 목적은 **API 서버**의 코드 변경을 테스트하기 위해서이므로, 동일한 버전의 microservice를 사용해야 합니다. 또한, **test 및 mirror API 서버**가 microservice에게 ***"동일한 요청"***을 보냈을 때 같은 결과를 받아야 microservice와 독립적인 테스트를 수행 할 수 있습니다. 이 요구 사항을 만족시키기 위한 두 가지 방법이 있습니다.

#### Choice 1 - Microservice 복제하기
**Test API 서버**와 **Mirror API 서버**가 사용하는 microservice를 다르게 합니다. 즉, 모든 microservice를 2개씩 띄웁니다.
- 장점: 2번 선택지와는 다르게 Traffic 중복 처리를 할 필요가 없습니다.
- 단점: Microservice가 너무 많습니다. 20개 이상의 Pod을 새로 띄워야 하고, 가격이 2배가 되고 AWS 영수증을 보면 마음이 아프게 됩니다. 또한, **Mirror API 서버**가 사용하는 microservice는 DB에 write 하면 안 되므로 모든 microservice에 대해 코드를 변경해야 합니다.

#### Choice 2 - Traffic **잘** 처리하기
같은 microservice를 사용하고, **mirror API 서버**에서 호출한 요청은 실제로 처리하는 대신 **test API 서버**에서 호출한 결과가 반환되도록 합니다.
- 장점: 1번 선택지와는 다르게 존재하는 microservice에 아무것도 할 필요가 없습니다.
- 단점: 중복 요청이 없고, 요청을 cache 할 수 있도록 **잘** 처리해야 합니다.

선택의 갈림길에서, Fitz님과의 회의를 통해 2번을 선택하게 되었습니다. 안타깝게도, Istio가 지원하는 단순한 network logic만으로는 요청을 **잘** 처리 할 수 없어, Backend Dev1팀에서는 ***mirror-cache***를 개발했습니다.
- (1 ~ 2): **Test API 서버**와 **mirror API 서버**의 모든 outbound http call을 받아서
- (3 ~ 5): **API 서버**에서 보낸 outbound http call을 원래 microservice에 요청하고 그 결과를 캐시 한 다음 반환합니다.
- (6): 그리고 **mirror API 서버**에서 보낸 ***"동일한 요청"***에 대해서는 캐시 된 결과를 반환합니다.

![mirror-cache-overview]({{"/assets/2020-06-02-azar-mirror-2/01-mirror-cache.png"}})
(***mirror-cache***에 대한 더 자세한 내용은 곧 올라올 서버 제작기 3편을 참고하시기 바랍니다)


마침내, microservice outbound http call 처리를 위해 DevOps 팀이 해야 할 일을 명확하게 정할 수 있었습니다.
- (A) **Test API 서버**와 **mirror API 서버**의 모든 outbound http call은 ***mirror-cache***로 routing 해야 함
- (B) Routing시 ***mirror-cache***가 어떤 **API 서버**에서 route 된 traffic인지 알 수 있도록 특정 header 값을 추가해야 함
- (C) API call에서 생성된 outbound http call을 ***mirror-cache***로 routing 할 때 ***"동일한 요청"***을 확인할 수 있도록 식별자를 header에 추가해야 함

이제부터, 위 요구사항을 어떻게 Istio만으로 해결했는지 설정 (그리고 많은 yaml)과 함께 설명하겠습니다.


# 1 - Istio Mirroring
Istio의 traffic mirroring 기능[[3]](https://istio.io/docs/tasks/traffic-management/mirroring/)을 사용하면 설정 몇 줄로 모든 inbound traffic을 지정된 곳으로 mirroring 할 수 있습니다. 
모든 **Test API 서버** traffic은 AWS ALB를 거쳐서 Istio ingressgateway로 들어오므로, 이 설정을 적용하게 되면 ingressgateway에서 요청을 복제하여 원래의 **Test API pod**과 **mirror API pod**에 동시에 전송합니다. Istio의 mirroring 요청은 fire & forget으로, **mirror API pod**에 보낸 요청의 timeout / 성공 실패 여부에 상관없이 사용자는 **Test API pod**의 응답만 받게 됩니다.

아래 설정은 `azar` namespace에 있는 `api` service로 들어온 모든 http 요청을 `azar-mirror` namespace의 `api` service로 보내도록 합니다.
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: api
  namespace: azar
spec:
  hosts:
    - api
  http:
    - route:
        - destination:
            host: api
      mirror:
        host: api.azar-mirror.svc.cluster.local
      mirror_percent: 100
```
매우 간단하게 끝났습니다.


# 2.A & 2.B - Istio Virual Service
Istio의 virtual service는 mirroring이나 단순 routing 외에도 많은 일을 할 수 있습니다. `http[*].match[*].sourceLabels`를 사용하여 특정 label을 가지고 있는 pod에서 온 요청만 선택할 수 있습니다. 그리고 `http.headers.request.set`을 사용하여 request header에 특정 값을 추가 할 수도 있습니다.

먼저, `azar` namespace에 있는 **Test API 서버**에는 `app=api, stack=test` label을, `azar-mirror` namespace에 있는 **mirror API 서버**에는 `app=api, stack=mirror` label을 붙였습니다. 그리고 `tiny-microservice`에 대한 VirtualService를 정의했습니다. 정의한 VirtualService는 3개의 route rule을 정의합니다.
- `app=api, stack=mirror` label을 가지고 있는 pod (**mirror API 서버**)에서 `tiny-microservice`를 호출한 경우 `X-Azar-Mirror: "true"` header를 붙여서 `mirror-cache`로 route
- `app=api, stack=test` label을 가지고 있는 pod (**Test API 서버**)에서 `tiny-microservice`를 호출한 경우 `X-Azar-Mirror: "false"` header를 붙여서 `mirror-cache`로 route
- 그 외의 모든 경우 `tiny-microservice`로 route

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: tiny-microservice
  namespace: azar
spec:
  hosts:
    - tiny-microservice
  http:
    - match:
        - sourceLabels:
            app: api
            stack: mirror
      headers:
        request:
          set:
            X-Azar-Mirror: "true"
      route:
        - destination:
            host: mirror-cache.azar.svc.cluster.local
    - match:
        - sourceLabels:
            app: api
            stack: test
      headers:
        request:
          set:
            X-Azar-Mirror: "false"
      route:
        - destination:
            host: mirror-cache.azar.svc.cluster.local
  - route:
      - destination:
          host: tiny-microservice
```
역시 매우 간단하게 끝났습니다.


# 2.C - Istio Tracing
**Test API 서버**의 코드와 **mirror API 서버**의 코드가 다를 수 있어 ***"동일한 요청"***인지 판별할 때 단순히 http method, url, header, body만 사용해서는 안 됩니다.

다행히도, Istio는 Envoy의 Distributed Tracing 기능을 사용[[4]](https://istio.io/docs/tasks/observability/distributed-tracing/overview/)하고 있습니다. Istio mesh는 모든 http request header에 `x-request-id`가 존재하는지 확인하고, 없다면 UUID 값을 생성하여 추가합니다. 모든 microservice는 다른 microservice를 호출할 때 `x-request-id` 및 tracing에 필요한 다른 http headers를 전파해야 1번의 사용자 요청에 대해 1개의 올바른 trace를 얻을 수 있습니다. 또한, 원래의 **Test API 서버**로 들어오는 http request와 **mirror API 서버**로 들어오는 http request는 같은 `x-request-id`를 가지게 되므로, 이를 이용여 원본 요청과 복제된 요청의 쌍을 찾을 수 있습니다.

따라서, **API 서버**와 microservice에서 `x-request-id` 등 필요한 몇 가지 http headers를 전파해주기만 한다면 DevOps 팀의 작업 없이 동일한 API 요청으로 생성된 microservice http call을 식별 할 수 있습니다. 이제 앞 단락에서 주입했던 `x-azar-mirror`와 기본적으로 포함되는 `host` header를 살펴 `mirror-cache` microservice는 ***"동일한 요청"***을 식별할 수 있게 됩니다.

HTTP headers를 전파하기 위해서 다양한 microservice의 많은 부분에서 코드 변경이 필요하지만, Backend Dev 1팀은 `javaagent`를 사용하여 코드 변경 없이 이를 자동으로 수행하도록 했습니다. 좀 더 자세히 알아보고 싶으시다면, Fitz님의 [Kubernetes 환경을 위한 자바 에이전트 개발기](https://hyperconnect.github.io/2020/03/25/kube-agent.html) 글을 읽어보시기 바랍니다.


# Istio Envoy Filter
앞서 몇 단락에 걸쳐 적용한 설정은 완벽하게 작동합니다. 하지만 여전히 한계가 있습니다.
- 먼저, 10개가 넘는 microservice에 일일이 VirtualService를 설정하는 것은 힘들고 귀찮습니다. 게다가 Backend Dev 1팀에서 서비스를 추가할 때 미처 설정하지 못하고 넘어갈 수 있습니다.
- **API 서버**는 microservice 외에 다른 API도 호출합니다. 예를 들어, Facebook 로그인을 위해 `https://graph.facebook.com/`을 사용합니다. 이런 외부 http API call에 VirtualService를 적용하기 위해서는 먼저 ServiceEntry를 사용하여 mesh 안의 service로 등록시켜야 합니다. 도메인마다 ServiceEntry를 등록하고 VirtualService를 설정해야 해서 귀찮고, microservice와 마찬가지로 누락될 위험이 있습니다.

이 문제를 해결하기 위해 EnvoyFilter를 사용해보았습니다. Istio는 Envoy[[5]](https://www.envoyproxy.io/) 기반 Istio proxy를 모든 pod에 주입합니다. Istio control plane은 사용자가 생성한 VirtualService나 DestinationRule 같은 high-level 설정을 읽어 low-level 한 Envoy 설정으로 변환하여 proxy에 적용하는 방식으로 routing을 제어합니다. 이 과정에서 control plane이 생성한 Envoy 설정을 사용자가 직접 override 할 수 있도록 EnvoyFilter라는 설정이 존재합니다. 따라서 EnvoyFilter를 사용하면 Envoy를 원하는 대로 동작시킬 수 있습니다.

Envoy 설정을 덮어쓰기 위해서는 당연히 Envoy 설정을 알고 있어야 합니다. 주로 다음 4개의 리소스와 구글신에서 정보를 얻을 수 있었습니다.
- `istioctl`을 사용하여 pod의 Envoy dashboard [[6]](https://istio.io/docs/reference/commands/istioctl/#istioctl-dashboard-envoy)를 열고, `config_dump` 버튼을 누르면 해당 pod Envoy에 적용된 모든 설정을 JSON으로 확인 할 수 있습니다. 
- Envoy documentation [[7]](https://www.envoyproxy.io/docs/envoy/latest/API-v2/API/v2/route/route_components.proto#envoy-API-msg-route-route)을 참고하여 Envoy 설정의 의미를 파악 할 수 있습니다.
- Istio documentation [[8]](https://istio.io/docs/reference/config/networking/envoy-filter/)을 참고하여 EnvoyFilter object의 syntax를 확인 할 수 있습니다.
- Istio Pilot 코드 [[9]](https://github.com/istio/istio/tree/release-1.4/pilot/pkg/networking/core/v1alpha3/envoyfilter)를 참고하여 EnvoyFilter object의 적용 방법을 확인 할 수 있습니다.

Envoy config dump를 확인해보면 대략 다음과 같은 모습을 보실 수 있습니다.
```json
{
  "configs": [{
    "@type": "type.googleapis.com/envoy.admin.v2alpha.BootstrapConfigDump",
    "bootstrap": {"omitted": "too-long"},
    "last_updated": "2020-01-01T00:00:00.000Z"
  }, {
    "@type": "type.googleapis.com/envoy.admin.v2alpha.ClustersConfigDump",
    "version_info": "2020-01-01T00:00:00Z/00000",
    "static_clusters": ["omitted"],
    "dynamic_active_clusters": ["omitted"]
  }, {
    "@type": "type.googleapis.com/envoy.admin.v2alpha.ListenersConfigDump",
    "version_info": "2020-01-01T00:00:00Z/00000",
    "static_listeners": ["omitted"],
    "dynamic_active_listeners": ["omitted"]
  }, {
    "@type": "type.googleapis.com/envoy.admin.v2alpha.ScopedRoutesConfigDump"
  }, {
    "@type": "type.googleapis.com/envoy.admin.v2alpha.RoutesConfigDump",
    "static_route_configs": ["omitted"],
    "dynamic_route_configs": ["omitted"]
  }, {
    "@type": "type.googleapis.com/envoy.admin.v2alpha.SecretsConfigDump"
  }]
}
```

여기서는 routes를 일괄적으로 수정해야 하므로 `RoutesConfigDump`의 `dynamic_route_configs`를 확인하면 많은 route config을 볼 수 있습니다. 그중 이름이 `"80"`인 config를 확인해보겠습니다.
```json
{
  "version_info": "2020-05-04T08:54:41Z/32132",
  "route_config": {
    "name": "80",
    "virtual_hosts": ["omitted"],
    "validate_clusters": false
  },
  "last_updated": "2020-01-01T00:00:00.000Z"
}
```
이 route config는 outbound 80에 대한 route를 정의합니다. 이제 `virtual_hosts`를 보면 다음 설정과 거의 도메인 이름만 다른 수많은 route rule을 확인하실 수 있습니다. 
```json
{
  "name": "tiny-microservice.azar.svc.cluster.local:80",
  "domains": [
    "tiny-microservice.azar.svc.cluster.local",
    "tiny-microservice.azar.svc.cluster.local:80",
    "tiny-microservice.azar",
    "tiny-microservice.azar:80",
    "tiny-microservice.azar.svc.cluster",
    "tiny-microservice.azar.svc.cluster:80",
    "tiny-microservice.azar.svc",
    "tiny-microservice.azar.svc:80",
    "ip-of-tiny-microservice",
    "ip-of-tiny-microservice:80",
  ],
  "routes": [{
    "match": {
      "prefix": "/"
    },
    "route": {
      "cluster": "outbound|80||tiny-microservice.azar.svc.cluster.local",
      "timeout": "15s",
      "retry_policy": {"omitted": "too-long"},
      "max_grpc_timeout": "15s"
    },
    "metadata": {"omitted": "too-long"},
    "decorator": {"omitted": "too-long"},
    "typed_per_filter_config": {"omitted": "too-long"}
  }]
}
```
`domains`를 보면, Kubernetes에서 `tiny-microservice.azar`를 호출하는 데 사용 가능한 모든 domain이 나열되어 있습니다. `routes[0].route.cluster`는 이 도메인과 일치하는 요청의 routing 주소를 정의하고 있습니다. `outbound|80||tiny-microservice.azar.svc.cluster.local`인데, 이 cluster는 Envoy 설정 root에 있는 `ClustersConfigDump`에서 확인 할 수 있습니다. (여기서는 필요한 설정이 아니니 생략하겠습니다.)

결과적으로, `RoutesConfigDump`의 `dynamic_route_configs` 중 이름이 `"80"`인 config를 찾아 `virtual_hosts`의 모든 `routes[*].route.cluster`를 `mirror-cache`로 변경해야 합니다. 또한, `X-Azar-Mirror` header도 추가해야 합니다. 이를 모두 처리하는 EnvoyFilter 설정을 만들었습니다. 만들어진 설정을 보면, 내용은 대부분 직관적이라 쉽게 이해 할 수 있습니다.
- 아래의 모든 설정은 `workloadSelector.labels`를 사용하여 **test 및 mirror API 서버**에만 적용되도록 했습니다.
- `configPatches[*].applyTo`는 어떤 Envoy 설정을 덮어쓸 지 정의합니다. `virtual_hosts`내의 `routes`를 덮어쓰려면 `HTTP_ROUTE`를 사용해야 합니다.
- `configPatches[*].match`는 어떤 `HTTP_ROUTE`를 덮어쓸 지 정의합니다. 여기서는 이름이 `"80"`인 route config만 덮어씌워야 하므로 `routeConfiguration.name`을 사용했습니다.
- `configPatches[*].patch.operation`을 `MERGE`로 설정하여 기존에 존재하는 설정을 덮어쓰도록 하였습니다.
  - `value.request_headers_to_add`를 사용하여 `X-Azar-Mirror`를 추가했습니다.
  - `value.route.cluster`를 사용하여 `mirror-cache`로 routing 되도록 했습니다.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: azar-api-mirror
  namespace: azar
spec:
  workloadSelector:
    labels:
      app: api
      stack: test
  configPatches:
    - applyTo: HTTP_ROUTE
      match:
        context: ANY
        routeConfiguration:
          name: "80"
      patch:
        operation: MERGE
        value:
          request_headers_to_add:
            - header:
                key: X-Azar-Mirror
                value: "false"
          route:
            cluster: outbound|80||mirror-cache.azar.svc.cluster.local

---
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: azar-api-mirror
  namespace: azar-mirror
spec:
  workloadSelector:
    labels:
      app: api
      stack: test
  configPatches:
    - applyTo: HTTP_ROUTE
      match:
        context: ANY
        routeConfiguration:
          name: "80"
      patch:
        operation: MERGE
        value:
          request_headers_to_add:
            - header:
                key: X-Azar-Mirror
                value: "true"
          route:
            cluster: outbound|80||mirror-cache.azar.svc.cluster.local
```
마침내, 모든 HTTP 80 outbound에 대해 route를 `mirror-cache`로 지정했으므로, VirtualService에 route를 일일이 추가하지 않아도 모든 microservice에 대해 적용할 수 있습니다. 당연히 domain이 `*`인 route rule에도 적용되므로 microservice가 아닌 public http API도 적용됩니다.


# ???: 서버가 이상해요
이제 다 끝났다고 생각하고 퇴근을 했습니다. 다음 날, Backend Dev1팀은 QA 팀으로부터 프로필 사진 업로드가 안 된다는 버그를 제보받았고, 원인을 분석해서 AWS IAM credential이 이상하다고 알려주셨습니다.

Istio mesh에서 알 수 없는 traffic은 그대로 통과시킵니다. `"80"` route config 외에도 거의 모든 route config에는 아래와 비슷한 `allow_any` host가 있어 알 수 없는 traffic을 통과시킵니다.
```json
{
  "name": "allow_any",
  "domains": ["*"],
  "routes": [{
    "match": {
      "prefix": "/"
    },
    "route": {
      "cluster": "PassthroughCluster"
    },
    "typed_per_filter_config": {"omitted": "too-long"}
  }]
}
```
**API 서버**는 AWS credential을 가져오기 위해 `kube2iam` [[10]](https://github.com/jtblin/kube2iam)을 사용하고 있었는데, 위 EnvoyFilter 설정이 적용되면서 `PassthroughCluster`를 통해 Kubernetes node에 직접 전송되어야 할 요청이 `mirror-cache`를 통해 Kubernetes node에 전송되었고, `kube2iam`은 API pod에 대한 AWS credential이 아닌 `mirror-cache`에 대한 AWS credential을 주고 있었던 것이었습니다.

모든 HTTP 80 outbound를 수정했으므로, 다음 설정을 추가하여 AWS metadata는 `PassthroughCluster`를 사용하도록 route를 생성했습니다.
- `applyTo`를 `VIRTUAL_HOST`로 설정하고, `patch.operation`을 `ADD`로 설정하여 `virtual_hosts`에 host를 추가합니다.
- `patch.value.domains`는 AWS metadata의 주소인 `169.254.169.254`로 설정했습니다.
- `patch.value.routes[0].route.cluster`를 `PassthroughCluster`로 지정하여 Istio mesh를 거치지 않고 단순 forward하도록 만들었습니다.

```yaml
- applyTo: VIRTUAL_HOST
  match:
    context: ANY
    routeConfiguration:
      name: "80"
  patch:
    operation: ADD
    value:
      domains:
        - 169.254.169.254
        - 169.254.169.254:80
      name: aws
      routes:
        - match:
            prefix: /
          route:
            cluster: PassthroughCluster
```
Istio Pilot이 EnvoyFilter를 적용할 때에는 `configPatches`가 순서대로 적용되므로 이 host의 `route.cluster`는 `mirror-cache`로 덮어 쓰이지 않습니다. 또한, Envoy가 http traffic을 route 할 때는 `domains`가 가장 구체적인 host를 먼저 확인하기 때문에 기존에 존재하는 `allow_any` host 설정에 따라 `mirror-cache`로 routing 되지 않습니다. 이렇게 AWS IAM credential 문제를 해결할 수 있었습니다.


# Wrap Up
이 작업을 통해 다음 목표를 달성했습니다.
- Istio VirtualService 설정 3줄로 http traffic mirroring하기
- Istio EnvoyFilter를 사용해서 특정 pod의 routing을 원하는대로 수정하기

목표 달성을 위해 다양한 삽질을 했습니다.
- `istioctl`로 Envoy 설정을 확인하고, 무슨 뜻인지 Envoy 문서 읽으며 공부하기
- EnvoyFilter 설정을 잘했다고 생각했는데 계속 오류가 떠서 pilot 코드 뜯어보며 좌절하기
- 상상하지 못한 AWS metadata route rule 처리 실수 해결하기

삽질하면서 이런저런 생각이 들었습니다.
- 모르겠으면 직접 코드를 보는 것도 나쁘지 않음
- 세상에는 똑똑한 사람이 많고, 많이 배워야 함

하지만, 아직도 몇 가지 작업이 남아있습니다.
- Google, Apple 등 `:443`으로 요청하는 https outbound call 처리하기: `:80`으로 요청하면 `:443`으로 redirect 되므로 TLS origination 설정하여 처리해야 함
- 사내 문서 정리: 놀랍게도 이 블로그 글을 사내 문서보다 먼저 작성함
- 다른 곳에 EnvoyFilter 써볼 수 있는지 생각해보기


Mirroring test를 고민하고 있거나, Istio EnvoyFilter 사용에 조금이나마 도움이 되었으면 좋겠습니다.

읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 DevOps와 Backend 개발자분들의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)


# References
[1] [https://istio.io/](https://istio.io/)

[2] [https://kubernetes.io/](https://kubernetes.io/)

[3] [https://istio.io/docs/tasks/traffic-management/mirroring/](https://istio.io/docs/tasks/traffic-management/mirroring/)

[4] [https://istio.io/docs/tasks/observability/distributed-tracing/overview/](https://istio.io/docs/tasks/observability/distributed-tracing/overview/)

[5] [https://www.envoyproxy.io/](https://www.envoyproxy.io/)

[6] [https://istio.io/docs/reference/commands/istioctl/#istioctl-dashboard-envoy](https://istio.io/docs/reference/commands/istioctl/#istioctl-dashboard-envoy)

[7] [https://www.envoyproxy.io/docs/envoy/latest/API-v2/API/v2/route/route_components.proto#envoy-API-msg-route-route](https://www.envoyproxy.io/docs/envoy/latest/API-v2/API/v2/route/route_components.proto#envoy-API-msg-route-route)

[8] [https://istio.io/docs/reference/config/networking/envoy-filter/](https://istio.io/docs/reference/config/networking/envoy-filter/)

[9] [https://github.com/istio/istio/tree/release-1.4/pilot/pkg/networking/core/v1alpha3/envoyfilter](https://github.com/istio/istio/tree/release-1.4/pilot/pkg/networking/core/v1alpha3/envoyfilter)

[10] [https://github.com/jtblin/kube2iam](https://github.com/jtblin/kube2iam)
