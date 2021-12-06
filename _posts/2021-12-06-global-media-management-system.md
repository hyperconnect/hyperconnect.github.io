---
layout: post
date: 2021-12-06
title: Global Media Management System 개발
author: min.k
tags: media-management-system upload event edge-server
excerpt: 전세계에 위치한 사용자에게 Media Management System을 제공한 사례에 대해 소개합니다
last_modified_at: 2021-12-06
---
아자르는 전세계 230개 이상의 국가에서 Social Discovery 서비스를 제공하고 있습니다. 사용자들은 관계를 형성하기 위해 사진, 동영상, 음성 등 자신의 미디어를 서비스에 등록할 수 있습니다. 이러한 미디어 전송 행위는 전세계에 위치한 사용자들로부터 수행되며 이를 안정적으로 제공하기 위해 Media Management System을 개발하게 되었습니다. 본 게시물을 통해 해당 사례에 대해 소개하고자 합니다.


# 배경
아자르 서비스의 기존 미디어 업로드 방식은 Client가 직접 AWS S3 저장소에 직접 업로드를 수행하는 방식으로 이루어져 있었습니다. 따라서, 직접 Client 단말기에서 최종 저장소로 업로드를 수행하기 때문에 현황 파악이 어려운 문제가 있었습니다. 나아가, 각 나라 및 지역의 [ISP (Internet Service Provider)](https://en.wikipedia.org/wiki/Internet_service_provider)에서 네트워크 이슈가 발생할 경우, 해당 지역 인근에 위치한 사용자들은 업로드가 불가능한 상황이 발생합니다. 업로드 요청은 Client에서 AWS S3로 직접 전달되기에, 네트워크에 문제가 생긴 것인지 인지하는 것 조차도 어렵습니다. 인지할 수 없는 문제는 풀 수 없는 문제와 같습니다. 따라서, 각 Client에서 최종 저장소에 직접 파일 업로드를 수행하지 않고 서버를 통해 업로드를 수행하도록 개선하게 되었습니다.


# 목표
전세계에 위치한 사용자에게 Media Management System 제공


# 주요 기능
* Media Upload 기능
* Media Delete 기능
* Media Download 기능
* Media History 관리 기능


# 부가 기능
* Media History CDC 기능
* JWT 인증 기능
* JsonPath를 이용한 유연한 Property 추출 기능
* ISP Network Issue 대응 기능


# 방식
Edge Server와 Backbone Network를 활용하여 트래픽 전송을 가속화 합니다. 이를 통해 전세계 각 지역에 위치한 사용자는 Media Management System과의 데이터 전송을 고속으로 수행 할 수 있습니다.

![Media Management System]({{"/assets/2021-12-06-global-media-management-system/media_management_system.png"}})


# 구현
많은 사용자들이 동시에 대용량 업로드 요청을 수행하더라도 빠르고 안정적으로 처리할 수 있어야 합니다. 따라서, 전송할 Media의 전체 Byte를 Heap Memory에 모두 Load 하지 않고 작은 Chunk 단위로 쪼개 비동기 스트리밍 방식으로 업로드를 수행하도록 구현하였습니다. Server Application은 Spring Framework를 기반으로 하며 비동기 스트리밍 업로드를 위해 Webflux, Kotlin Coroutine를 활용합니다. Media Storage는 AWS S3를 사용하며, Media History Storage는 Distributed Database인 ScyllaDB를 사용합니다.


## Servlet Upload (Memory) - 1.6GB Video Upload
Servlet Upload에서 File에 Flush하지 않고 Memory에 Load하여 사용하는 방식입니다. 비효율적인 File I/O는 발생하지 않지만 OOM(Out of memory)에 취약합니다.
![Servlet Upload without File Flush]({{"/assets/2021-12-06-global-media-management-system/servlet_upload_without_file_flush.png"}})


## Servlet Upload (File) - 1.6GB Video Upload
Servlet Upload는 OOM 방지를 위해 Temporary File로 Write 후 그것을 읽는 방식으로 사용 가능합니다. 하지만, 매 요청마다 비효율적인 File I/O가 발생하며 Disk Full의 위험성이 있습니다.
![Servlet Upload with File Flush]({{"/assets/2021-12-06-global-media-management-system/servlet_upload_with_file_flush.png"}})


## Reactive Upload - 1.6GB Video Upload
전송할 데이터의 Byte를 여러개의 Chunk로 나누어 Memory에 Load하여 사용하는 방식입니다. 비동기 방식으로 컴퓨팅 자원을 상대적으로 효율적으로 사용 가능하며 File I/O가 발생하지 않습니다. 나아가, 작은 Chunk 단위로 메모리를 사용하여 OOM에 더 안전합니다. 따라서, Media Management System에서는 Reactive Upload 방식을 사용하였습니다.
![Reactive Upload]({{"/assets/2021-12-06-global-media-management-system/reactive_upload.png"}})


# Media History CDC
Media Management System은 요청 이력 관리를 위해 각 Media 전송 요청이 성공하면 Media History를 인접한 Datacenter에 위치한 ScyllaDB에 Write합니다. ScyllaDB는 Distributed Database로서 지속적으로 Datacenter간의 데이터 동기화 작업을 수행합니다. 이때, [CDC Platform](https://hyperconnect.github.io/2021/01/11/cdc-platform.html)을 활용하면 모든 Datacenter ScyllaDB에 기록된 Media History 데이터를 Kafka Cluster로 실시간 스트리밍 전송이 가능합니다. 이를 통해 각 국가 별 Media 요청 현황을 실시간으로 파악할 수 있습니다.

![Content History CDC]({{"/assets/2021-12-06-global-media-management-system/media_management_system_with_cdc.png"}})


# Media History Monitoring
Media History CDC를 통해 Kafka로 실시간 스트리밍 전송되는 Media History Event들은 [CDC Sink Platform](https://hyperconnect.github.io/2021/03/22/cdc-sink-platform.html)을 통해 OpenSearch로 적재되며 Grafana를 통해 Metric 현황을 시각화 할 수 있습니다. 이를 통해 전세계 국가별 Media 요청 현황을 실시간으로 모니터링할 수 있습니다. 이는 국가 별 네트워크 문제를 빠르게 탐지하고 대응할 수 있는 기반이 됩니다.


## Media Management System - Request Geo Map
다음 지표를 통해 실시간으로 전송되고 있는 전세계 국가 별 Media 요청 현황을 Geo Map 형태로 파악할 수 있습니다.

![Media Management System Geo Map]({{"/assets/2021-12-06-global-media-management-system/media_management_system_geo_map.png"}})


## Media Management System - Request Histogram
다음 지표를 통해 실시간으로 전송되고 있는 전세계 국가 별 Media 요청 현황을 Histogram 형태로 파악할 수 있습니다.

![Media Management System Upload Top 30]({{"/assets/2021-12-06-global-media-management-system/media_management_system_upload_top_30.png"}})


## Media Management System - Request Content Type
다음 지표를 통해 실시간으로 전송되고 있는 Media의 Content Type 현황을 파악할 수 있습니다.

![Media Management System Upload Content Type]({{"/assets/2021-12-06-global-media-management-system/media_management_system_upload_content_type.png"}})


## Media Management System - Request Content Length
다음 지표를 통해 실시간으로 전송되고 있는 Media의 Content Length 현황을 파악할 수 있습니다.

![Media Management System Upload Content Length]({{"/assets/2021-12-06-global-media-management-system/media_management_system_upload_content_length.png"}})


## Media Management System - Request Latency Percentile
다음 지표를 통해 각 Region 별 실시간으로 처리되고 있는 Media 전송 Latency Percentile 현황을 파악할 수 있습니다.

![Media Management System Upload Latency Percentile]({{"/assets/2021-12-06-global-media-management-system/media_management_system_upload_latency_percentile.png"}})


# ISP Network Issue
다양한 국가에 서비스를 제공할 경우 [ISP (Internet Service Provider)](https://en.wikipedia.org/wiki/Internet_service_provider)의 Network Issue를 경험할 수 있습니다. Media Management System에서는 ISP의 Network Issue 발생시 이를 해소하고 사용자에게 안정적으로 서비스를 제공하기 위한 여러 기술들을 활용하고 있습니다.


# HTTP Public Key Pinning
SSL/TLS 암호화 통신은 Man-in-the-middle Attack에 취약하여 이를 최대한 방지하기 위한 방법이 필요합니다. 사용하려는 특정 인증서를 고정하는 방식을 [HTTP Public Key Pinning](https://en.wikipedia.org/wiki/HTTP_Public_Key_Pinning) 이라고 하며 이러한 기법을 사용합니다. 이때, Client가 의도하는 인증서가 맞는지 구분하기 위해 서버는 Cert Digest를 제공합니다. Client는 이를 이용하여 본인이 의도하는 인증서가 맞는지 대조합니다. 이를 통해 해커가 만든 사설 인증서인지, 회사 내에서 올바르게 만든 사설 인증서인지 대조하여 검증을 수행할 수 있습니다. Media Management System에서는 사용자 미디어 보안을 위해 HTTP Public Key Pinning 기법을 활용하고 있습니다.


# Edge Server & Backbone Network
Media Management System을 이용하는 다양한 지역의 사용자들에게 일관된 성능을 제공하기 위해 여러 가지 제품을 고려 하였습니다. 사내에서 AWS 제품을 활용하고 있어 AWS 제품에 대해 높은 우선순위를 두어 테스트를 진행하였습니다. AWS Global Accelerator는 내부적으로 AWS Backbone과 Edge Server를 활용하여 트래픽 전송을 가속화합니다. 또한, 통합된 접근 방식을 제공하고 적용이 비교적 간단하여 AWS Global Accelerator을 우선적으로 적용하였습니다. 하지만, AWS Global Accelerator 사용시 P90 이상의 Long tail latency가 지연되는 현상이 있었습니다. 이를 해소하기 위해 전세계 각 지역에 더 많은 Edge Server를 확보하고 있는 Cloudflare를 활용하도록 변경하였고 Long tail latency 지연 문제를 해소할 수 있었습니다.

나아가 정확한 비교를 위해 AWS Global Accelerator가 아닌 Amazon Cloudfront를 사용하여 Cloudflare와 비교 해보았습니다. 하지만 Cloudflare에서 Amazon Cloudfront로 전환시 AWS Global Accelerator와 동일하게 Long tail latency가 지연되는 현상을 확인할 수 있었습니다. 이에 따라 Media Management System에 Cloudflare 적용을 결정하게 되었습니다.

이를 통해 Application에서 측정되는 P99 기준 Long tail latency는 최대 180초에서 1.5초로 11,900% 개선되었습니다. 각 국가 및 지역별 Local Network 상황은 다르며 사용자와 Egde Server까지의 거리가 멀 경우 Network Latency는 큰 편차를 보일 수 있습니다.


## AWS Global Accelerator -> Cloudflare
![AWS Global Accelerator -> Cloudflare]({{"/assets/2021-12-06-global-media-management-system/global_accelerator_to_cloudflare.png"}})


## Cloudflare -> Amazon Cloudfront
![Cloudflare -> Amazon CloudFront]({{"/assets/2021-12-06-global-media-management-system/cloudflare_to_cloudfront.png"}})


# 결론
Media Management System을 개발하여 다음과 같은 효과를 얻을 수 있었습니다.
* 각 국가에서 발생하는 Media 요청 현황을 측정 가능하도록 개선
* 각 국가 및 지역 ISP에서 네트워크 문제가 발생할 경우 Server에서 자체적으로 대응할 수 있도록 개선
* AWS Edge Server & Backbone -> Cloudflare Edge Server & Backbone 전환, P99 기준 Long tail latency 최대 180초에서 1.5초로 11,900% 개선


# Reference

[1] [CDC Platform](https://hyperconnect.github.io/2021/01/11/cdc-platform.html)  
[2] [CDC Sink Platform](https://hyperconnect.github.io/2021/03/22/cdc-sink-platform.html)  
[3] [AWS Global Accelerator](https://aws.amazon.com/ko/global-accelerator/?blogs-global-accelerator.sort-by=item.additionalFields.createdDate&blogs-global-accelerator.sort-order=desc&aws-global-accelerator-wn.sort-by=item.additionalFields.postDateTime&aws-global-accelerator-wn.sort-order=desc)  
[4] [Amazon Cloudfront](https://aws.amazon.com/ko/cloudfront/)  
[5] [Cloudflare](https://www.cloudflare.com/ko-kr/network/)  
[6] [AWS Global Accelerator vs Amazon Cloudfront](https://aws.amazon.com/ko/global-accelerator/faqs/)
