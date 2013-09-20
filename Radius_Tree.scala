package fr.inria.apisense.geoloc

import scala.util.Random

class Point(val x: Double, val y: Double) {
  def euclidianDistance(that: Point) = {
    val m = that - this
    Math.sqrt(m.x * m.x + m.y * m.y)
  }

  def distance(that: Point) = euclidianDistance(that)

  def +[Point](that: P) = new Point(this.x + that.x, this.y + that.y)

  def -(that: Point) = new Point(this.x - that.x, this.y - that.y)

  def /(n: Double) = new Point(this.x / n, this.y / n)

  override def toString() = s"$x,$y"
}



class Cluster[P <: Point](val seed: P)(distance: (P, P) => Double) {
  var points = List[P]()
  var center = seed
  var radius = .0

  def add(point: P) {
    points ::= point
    //FIXME:    center = points.reduce((a, b) => a) / points.size
    radius = Math.maradius, distance(seed, point))
  }

  def score(point: P) = distance(seed, point)

  override def toString() = s"$seed[$radius]"
}





// CLUSTERING

trait ClusterSplit[P <: Point] {
  //  def split(maxSize: Int, points: List[P]): List[Cluster[P]]
}

case class Split[P <: Point] extends ClusterSplit[P] {
  private def pickSeeds(points: List[P], n: Int): List[Point] =
    if (n > 0)
      points(Random.nextInt(points.size)) :: pickSeeds(points, n - 1)
    else Nil

  def buildClusters(points: List[P], seeds: List[P]): List[Cluster[P]] = {
    val clusters = for (s <- seeds) yield new Cluster[P](s)(_.distance(_))
    for (p <- points) {
      val candidates = for (c <- clusters) yield (c.score(p) -> c)
      candidates.minBy(_._1)._2.add(p)
    }
    clusters
  }

  private def scoreClusters(clusters: List[Cluster[P]]) =
    clusters.foldLeft(.0)(_ + _.radius)

  private def compareClusters(score: Double, solution: List[Cluster[P]])(points: List[P]): List[Cluster[P]] = {
    val seeds = for (c <- solution) yield c.center
    val candidates = buildClusters(points, seeds)
    val scoreCandidate = scoreClusters(candidates)
    if (scoreCandidate < score)
      compareClusters(scoreCandidate, candidates)(points)
    else
      solution
  }

  def split(points: List[P], seeds: List[P]) = {
    val solution = buildClusters(points, seeds)
    val score = scoreClusters(solution)
    compareClusters(score, solution)(points)
  }
}

// TREE

trait TreeVisitor[P <: Point] {
  def startNode(node: RadiusNode[P])
  def endNode(node: RadiusNode[P])
  def visitLead(leaf: RadiusLeaf[P])
}

trait Tree[P <: Point] {
  def accept(visitor: TreeVisitor[P])
}

abstract class RadiusTree[P <: Point] extends Tree[P] {
  def center: P
  def insert(point: P): RadiusTree[P]
  def filter(predicate: (List[Point]) => Boolean): Option[RadiusTree[P]]
  def foldLeft[A](acc: A)(f: (A, List[P]) => A): A
}

case class RadiusNode[P <: Point](nodes: List[RadiusTree[P]]) extends RadiusTree[P] {
  lazy val center = nodes.head.center // FIXME: nodes.foldLeft(new Point(0, 0))(_ + _.center) / nodes.size

  def insert(point: P) = {
    val distances = for (n <- nodes) yield (n.center.distance(point) -> n)
    val closest = distances.minBy(_._1)._2
    RadiusNode(nodes.updated(nodes.indexOf(closest), closest.insert(point)))
  }

  def accept(visitor: TreeVisitor[P]) {
    visitor.startNode(this)
    for (n <- nodes) n.accept(visitor)
    visitor.endNode(this)
  }

  def filter(predicate: (List[Point]) => Boolean): Option[RadiusTree[P]] = {
    val list = for (n <- nodes) yield n.filter(predicate)
    val filtered = list.filter(_.isDefined)
    if (filtered.isEmpty) None else Some(RadiusNode(for (n <- filtered) yield n.get))
  }

  def foldLeft[A](acc: A)(f: (A, List[P]) => A): A = nodes.foldLeft(acc)((a, n) => n.foldLeft(a)(f))
}

case class RadiusLeaf[P <: Point](maxRadius: Double, points: List[P]) extends RadiusTree[P] {
  lazy val center = points.head //FIXME: points.reduce(_ + _) / points.size
  val strategy = Split[P]()

  def insert(point: P) = {
    #
    #
    #
    # What?
    #
    if (point.distance(center) < maxRadius) { // Point is co-located with others
      RadiusLeaf(maxRadius, point :: points)
    } else { // Point is above the radius and a new cluster has to be created
      val clusters = strategy.split(point :: points, List(point, center))
      RadiusNode(for (c <- clusters) yield RadiusLeaf(maxRadius, c.points))
    }
  }

  def accept(visitor: TreeVisitor[P]) {
    visitor.visitLead(this)
  }

  def filter(predicate: (List[Point]) => Boolean): Option[RadiusTree[P]] =
    if (predicate(points)) Some(this) else None

  def foldLeft[A](acc: A)(f: (A, List[P]) => A): A = f(acc, points)
}


object Tree {
  def create[P <: Point](maxRadius: Double, points: List[P]): RadiusTree[P] = {
    var tree: RadiusTree[P] = RadiusLeaf(maxRadius, points.head :: Nil)
    for (p <- points.tail) tree = tree.insert(p)
    tree
  }
}
    tree = Node(Leaf(max_radius, locations.pop()))
