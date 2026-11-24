import { Bike, Car, Footprints, Train } from "lucide-react";

export const getModeIcon = (mode: string) => {
    switch (mode.toLowerCase()) {
      case "metro":
      case "train":
        return Train;
      case "cycling":
      case "bicycle":
        return Bike;
      case "walking":
        return Footprints;
      default:
        return Car;
    }
  };
