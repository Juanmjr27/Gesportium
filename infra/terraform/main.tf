terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 4.5"
    }
  }
}

provider "docker" {}

resource "docker_network" "gesportium" {
  name = "gesportium-tf-net"
}
